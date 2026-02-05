from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.urls import reverse
from admin.access.models import UserAuth
from admin.users.models import Users
from admin.access.serializers import UserAuthSerializer, VerifyOtpSerializer, LoginSerializer, UnifiedLoginSerializer, SignupSerializer, LogoutSerializer, CreateAccountSerializer
from admin.access.permissions import IsSuperAdmin
from django.shortcuts import render
from django.core.mail import send_mail
import random
from drf_yasg.utils import swagger_auto_schema
from django.conf import settings
from twilio.rest import Client
from admin.access.authenticator import get_tokens_for_user
from rest_framework_simplejwt.tokens import RefreshToken
from admin.access import config
from django.contrib.auth.hashers import check_password, make_password
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.models import User as AdminUser
from django.contrib.sessions.models import Session
from django.contrib.auth import logout as django_logout

class AuthViewSet(viewsets.GenericViewSet):
    queryset = UserAuth.objects.all()
    serializer_class = UserAuthSerializer
    @swagger_auto_schema(request_body=VerifyOtpSerializer)
    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        auth_record = UserAuth.objects.get(user=user)
        auth_record.is_verified = True
        auth_record.save()
        
        return Response({
            "message": "OTP verified successfully",
            "role": user.role,
            "user_id": user.id,
        })

    @swagger_auto_schema(request_body=UnifiedLoginSerializer)
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = UnifiedLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']

        try:
            auth_record = UserAuth.objects.get(user=user)
            if not auth_record.is_verified:
                return Response({"error": "Account not verified. Please verify your OTP to approve your account."}, status=status.HTTP_403_FORBIDDEN)

            if auth_record.is_logged_in:
                 return Response({"error": "User already logged in"}, status=status.HTTP_400_BAD_REQUEST)
            
            auth_record.is_logged_in = True
            auth_record.save()
        except UserAuth.DoesNotExist:
             # Should not happen typically if registered,but handle safely
             pass

        tokens = get_tokens_for_user(user)
        
        return Response({
            "message": "Login Successful",
            "role": user.role,
            "user_id": user.id,
            "access": tokens['access'],
            "refresh": tokens['refresh']
        })
             
    @swagger_auto_schema(methods=['post'], request_body=SignupSerializer)
    @action(detail=False, methods=['post'], url_path='signup')
    def signup(self, request):
        data = request.data.copy()
        if 'username' not in data:
            if 'email' in data:
                data['username'] = data['email']
            elif 'phone' in data:
                data['username'] = data['phone']
        
        serializer = SignupSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        email = None
        phone = None
        if '@' in username:
            email = username
        else:
            phone = username 
        try:
            user = Users.objects.create(
                email=email,
                phone=phone,
                name=email.split('@')[0] if email else f"User{phone}",
                role='USER',
                password_hash=make_password(password) if password else None
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        # UserAuth is created by signal
        auth_record = UserAuth.objects.get(user=user)
        otp = str(random.randint(1000, 9999))
        auth_record.otp = otp
        auth_record.save()
        print(f"DEBUG OTP: {otp}")
        if email:
            print(f"Attempting to send email to: {email}")
            try:
                send_mail(
                    'Your Swiggy Signup OTP',
                    f'Your Signup OTP is: {otp}',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False
                )
            except Exception as e:
                return Response({"error": f"Failed to send email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        elif phone:
            try:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                client.messages.create(
                    body=f'Your Swiggy Signup OTP is: {otp}',
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone
                )
            except Exception as e:
                print(f"Failed to send SMS: {e}")

        return Response({
            "message": "User registered. OTP sent for verification.", 
            "user_id": user.id,
            "is_otp_sent": True
        }, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(request_body=LogoutSerializer)
    @action(detail=False, methods=['post'])
    def logout(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = serializer.validated_data.get('user')
            admin_user = serializer.validated_data.get('admin_user')
            django_logout(request)
            cleaned_sessions = 0
            if user:
                 try:
                    auth_record = UserAuth.objects.get(user=user)
                    auth_record.is_logged_in = False
                    auth_record.save()
                    cleaned_sessions += 1
                 except UserAuth.DoesNotExist:
                    pass
            if admin_user:
                 sessions = Session.objects.filter(expire_date__gte=timezone.now())
                 for session in sessions:
                    data = session.get_decoded()
                    if str(data.get('_auth_user_id')) == str(admin_user.id):
                        cleaned_sessions += 1
                        session.delete()
            return Response({
                "message": f"Logout Successful. {cleaned_sessions} active sessions terminated."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=CreateAccountSerializer)
    @action(detail=False, methods=['post'], permission_classes=[IsSuperAdmin])
    def create_account(self, request):
        serializer = CreateAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        role = serializer.validated_data['role']
        admin_type = serializer.validated_data.get('admin_type', 'NONE')

        email = None
        phone = None
        if '@' in username:
            email = username
        else:
            phone = username

        # Check if user already exists before sending email
        if Users.objects.filter(email=email).exists() or (phone and Users.objects.filter(phone=phone).exists()):
             return Response({"error": "User with this email/phone already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare data for token
        user_data = {
            'email': email,
            'phone': phone,
            'name': email.split('@')[0] if email else f"User{phone}",
            'role': role,
            'admin_type': admin_type,
            'password_hash': make_password(password)
        }
        
        from django.core import signing
        # Sign and dump the data into a token
        token = signing.dumps(user_data)
        
        approve_link = f"{request.scheme}://{request.get_host()}/auth/by_super_admin/approve_account/?token={token}"
        reject_link = f"{request.scheme}://{request.get_host()}/auth/by_super_admin/reject_account/?token={token}"

        print(f"DEBUG APPROVE LINK: {approve_link}")
        print(f"DEBUG REJECT LINK: {reject_link}")

        if email:
            try:
                message = f"""
Welcome to Swiggy!
Your account has been created by the Super Admin.
Please choose an action to activate your account:
Approve (Create Account): {approve_link}
Reject (Ignore): {reject_link}
"""
                send_mail(
                    'Swiggy Account Action Required',
                    message, 
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False
                )
            except Exception as e:
                 print(f"Failed to send email: {e}")
        elif phone:
             try:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                client.messages.create(
                    body=f'Swiggy Account Setup.\nApprove: {approve_link}\nReject: {reject_link}',
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone
                )
             except Exception as e:
                print(f"Failed to send SMS: {e}")

        return Response({
            "message": "Account setup initiated. Approval links sent to user. Account will be created upon approval.",
            # "token": token # Optional: return token for debug if needed, but safer not to expose if not needed
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], authentication_classes=[])
    def approve_account(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        from django.core import signing
        try:
            # Load data from token (valid for 48 hours)
            user_data = signing.loads(token, max_age=172800)
            
            # Check existence again in case it was created in the meantime
            if Users.objects.filter(email=user_data['email']).exists() or (user_data['phone'] and Users.objects.filter(phone=user_data['phone']).exists()):
                 return Response({"message": "Account already registered or verified."}, status=status.HTTP_200_OK)
            
            # Create User
            user = Users.objects.create(
                email=user_data['email'],
                phone=user_data['phone'],
                name=user_data['name'],
                role=user_data['role'],
                admin_type=user_data['admin_type'],
                password_hash=user_data['password_hash']
            )

            # Determine Auth Type
            # UserAuth is created by signal. We just need to verify it.
            auth_record = UserAuth.objects.get(user=user)
            auth_record.is_verified = True
            auth_record.save()
            
            return Response({"message": "Account Successfully Created and Approved. You can now login."}, status=status.HTTP_201_CREATED)
            
        except signing.SignatureExpired:
             return Response({"error": "Link has expired"}, status=status.HTTP_400_BAD_REQUEST)
        except signing.BadSignature:
             return Response({"error": "Invalid link"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
             return Response({"error": f"Creation failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], authentication_classes=[])
    def reject_account(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        from django.core import signing
        try:
            signing.loads(token, max_age=172800)
            # We just validate the token. Since no account exists, we do nothing.
            return Response({"message": "Request Rejected. No account was created."}, status=status.HTTP_200_OK)
            
        except signing.SignatureExpired:
             return Response({"error": "Link has expired"}, status=status.HTTP_400_BAD_REQUEST)
        except signing.BadSignature:
             return Response({"error": "Invalid link"}, status=status.HTTP_400_BAD_REQUEST)
