from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.access.models import UserAuth
from admin.users.models import Users
from admin.access.serializers import UserAuthSerializer, VerifyOtpSerializer, LoginSerializer, UnifiedLoginSerializer, SignupSerializer
from django.shortcuts import render
from django.core.mail import send_mail
import random
from drf_yasg.utils import swagger_auto_schema
from django.conf import settings
from twilio.rest import Client
from admin.access.authenticator import get_tokens_for_user
from admin.access import config
from django.contrib.auth.hashers import check_password, make_password

class AuthViewSet(viewsets.GenericViewSet):
    queryset = UserAuth.objects.all()
    serializer_class = UserAuthSerializer
    @swagger_auto_schema(request_body=VerifyOtpSerializer)
    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        data = request.data
        contact = data.get('contact')
        otp = data.get('otp')
        
        if not contact or not otp:
             return Response({"error": "Contact and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)
        user = None
        if '@' in contact:
             user = Users.objects.filter(email=contact).first()
        else:
             user = Users.objects.filter(phone=contact).first()

        if not user:
            return Response({"error": "User not found for provided contact"}, status=status.HTTP_404_NOT_FOUND)

        try:
            auth_record = UserAuth.objects.get(user=user)
            if auth_record.otp == otp:
                auth_record.is_verified = True
                auth_record.save()
                tokens = get_tokens_for_user(user)
                
                return Response({
                    "message": "Login Successful",
                    "role": user.role,
                    "user_id": user.id,
                    "access": tokens['access'],
                    "refresh": tokens['refresh']
                })
            else:
                return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        except UserAuth.DoesNotExist:
            return Response({"error": "OTP request not found"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=UnifiedLoginSerializer)
    @action(detail=False, methods=['post'])
    def login(self, request):
        data = request.data
        contact = data.get('contact')
        password = data.get('password')

        if not contact or not password:
            return Response({"error": "Contact and Password are required"}, status=status.HTTP_400_BAD_REQUEST)
        is_email = '@' in contact
        user = None
        
        if is_email:
            user = Users.objects.filter(email=contact).first()
        else:
            user = Users.objects.filter(phone=contact).first()

        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if user.password_hash and check_password(password, user.password_hash):
            tokens = get_tokens_for_user(user)
            return Response({
                "message": "Login Successful",
                "role": user.role,
                "user_id": user.id,
                "access": tokens['access'],
                "refresh": tokens['refresh']
            })
        else:
             return Response({"error": "Invalid Password"}, status=status.HTTP_401_UNAUTHORIZED)
             
    @swagger_auto_schema(methods=['post'], request_body=SignupSerializer)
    @action(detail=False, methods=['post'], url_path='signup')
    def signup(self, request):
        """
        Public endpoint for User registration.
        1. Creates User with provided credentials (Contact + Password).
        2. Sends OTP for verification.
        """
        data = request.data.copy()
        contact = data.get('contact') or data.get('email') or data.get('phone')
        email = data.get('email')
        phone = data.get('phone')
        if 'contact' in data:
            contact = data['contact']
            if '@' in contact:
                email = contact
            else:
                phone = contact
        
        if email and Users.objects.filter(email=email).exists():
            return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        if phone and Users.objects.filter(phone=phone).exists():
             return Response({"error": "User with this phone already exists"}, status=status.HTTP_400_BAD_REQUEST)
             
        data['role'] = 'USER' 
        password = data.pop('password', None) 
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

        auth_record, created = UserAuth.objects.get_or_create(user=user, defaults={'auth_type': 'USER'})
        otp = str(random.randint(1000, 9999))
        auth_record.otp = otp
        auth_record.save()
        if email:
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

    @swagger_auto_schema(methods=['post'])
    @action(detail=False, methods=['post'])
    def logout(self, request):
        from django.contrib.auth import logout
        logout(request)
        return Response({"message": "Logged out successfully. Please remove tokens from client."})
