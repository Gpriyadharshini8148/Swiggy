from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.access.models import UserAuth
from admin.users.models import Users
from admin.access.serializers import UserAuthSerializer, VerifyOtpSerializer, LoginSerializer, UnifiedLoginSerializer, SignupSerializer, LogoutSerializer
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

        auth_type_mapping = {
            'USER': 'USER',
            'ADMIN': 'ADMIN',
            'SUPERADMIN': 'ADMIN',
        }
        assigned_auth_type = 'USER' # Default
        if user.role == 'ADMIN':
            if user.admin_type == 'RESTAURANT':
                assigned_auth_type = 'RESTAURANT'
            elif user.admin_type == 'DELIVERY':
                assigned_auth_type = 'DELIVERY'
            else:
                assigned_auth_type = 'ADMIN'
        elif user.role == 'SUPERADMIN':
             assigned_auth_type = 'SUPERADMIN'
        
        auth_record, created = UserAuth.objects.get_or_create(user=user, defaults={'auth_type': assigned_auth_type})
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
