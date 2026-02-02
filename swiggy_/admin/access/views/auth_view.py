from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.access.models import UserAuth
from admin.users.models import Users
from admin.access.serializers import UserAuthSerializer, SendOtpSerializer, VerifyOtpSerializer, LoginSerializer, UnifiedLoginSerializer
from django.shortcuts import render
from django.core.mail import send_mail
import random
from drf_yasg.utils import swagger_auto_schema
from django.conf import settings
from twilio.rest import Client
from admin.access.authenticator import get_tokens_for_user
from admin.access import config



class AuthViewSet(viewsets.GenericViewSet):
    queryset = UserAuth.objects.all()
    serializer_class = UserAuthSerializer

    @swagger_auto_schema(request_body=SendOtpSerializer)
    @action(detail=False, methods=['post'])
    def send_otp(self, request):
        data = request.data
        email = data.get('email')
        phone = data.get('phone')

        if not email and not phone:
            return Response({"error": "Email or phone number is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = None
        if email:
            user = Users.objects.filter(email=email).first()
            if not user:
                user = Users.objects.create(
                    email=email,
                    name=email.split('@')[0],
                    role='USER'
                )
        elif phone:
            user = Users.objects.filter(phone=phone).first()
            if not user:
                if not phone.strip():
                    return Response({"error": "Phone number cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)
                user = Users.objects.create(
                    phone=phone,
                    name=f"User{phone}",
                    role='USER'
                )

        otp = str(random.randint(1000, 9999))
        
        # Ensure auth_type is set if creating new auth record
        defaults = {'auth_type': user.role if user.role else 'USER'}
        auth_record, created = UserAuth.objects.get_or_create(user=user, defaults=defaults)
        
        auth_record.otp = otp
        auth_record.save()

        if email:
            try:
                send_mail(
                    'Your Swiggy Login OTP',
                    f'Your OTP is: {otp}',
                    'noreply@swiggy.local',
                    [email],
                    fail_silently=False
                )
            except Exception as e:
                print(f"Failed to send email: {e}")

        if phone:
            try:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                message = client.messages.create(
                    body=f'Your Swiggy Login OTP is: {otp}',
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone
                )
            except Exception as e:
                print(f"Failed to send SMS: {e}")
        
        return Response({"message": "OTP sent successfully", "user_id": user.id, "is_new_user": False})

    @swagger_auto_schema(request_body=VerifyOtpSerializer)
    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        data = request.data
        otp = data.get('otp')
        email = data.get('email')
        phone = data.get('phone')
        
        user = None
        if email:
            user = Users.objects.filter(email=email).first()
        elif phone:
            user = Users.objects.filter(phone=phone).first()

        if not user:
            return Response({"error": "User not found for provided contact"}, status=status.HTTP_404_NOT_FOUND)

        try:
            auth_record = UserAuth.objects.get(user=user)
            if auth_record.otp == otp:
                auth_record.is_verified = True
                auth_record.save()
                
                # Generate Tokens
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
        otp = None # OTP not accepted in login initiation

        if not contact:
            return Response({"error": "Contact (email or phone) is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Determine if contact is email or phone
        is_email = '@' in contact
        user = None
        
        if is_email:
            user = Users.objects.filter(email=contact).first()
        else:
            user = Users.objects.filter(phone=contact).first()

        # If user doesn't exist, create one (standard behavior for OTP flow, usually)
        # But for Admin login, user must exist.
        if not user:
            if password: # If password provided, implies Admin attempt, but user not found
                 return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Create new user for OTP flow
            if is_email:
                user = Users.objects.create(email=contact, name=contact.split('@')[0], role='USER')
            else:
                user = Users.objects.create(phone=contact, name=f"User{contact}", role='USER')

        # Role Based Logic
        if user.role == 'ADMIN':
            if not password:
                return Response({"error": "Password required for Admin login"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify Password (simplistic check as per previous context)
            try:
                auth_record = UserAuth.objects.get(user=user)
                if auth_record.password_hash == password:
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
            except UserAuth.DoesNotExist:
                 return Response({"error": "Admin auth record not found"}, status=status.HTTP_400_BAD_REQUEST)

        else:
            # User / Restaurant / Delivery Flow (OTP)
            auth_record, created = UserAuth.objects.get_or_create(user=user, defaults={'auth_type': user.role})

            # Send OTP
            new_otp = str(random.randint(1000, 9999))
            auth_record.otp = new_otp
            auth_record.save()

            if is_email:
                try:
                    send_mail(
                        'Your Swiggy Login OTP',
                        f'Your OTP is: {new_otp}',
                        'noreply@swiggy.local',
                        [contact],
                        fail_silently=False
                    )
                except Exception as e:
                    print(f"Failed to send email: {e}")
            else:
                try:
                    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                    client.messages.create(
                        body=f'Your Swiggy Login OTP is: {new_otp}',
                        from_=settings.TWILIO_PHONE_NUMBER,
                        to=contact
                    )
                except Exception as e:
                    print(f"Failed to send SMS: {e}")

            return Response({
                "message": "OTP sent successfully. Please verify using /api/auth/verify_otp/", 
                "is_otp_sent": True
            })

    @action(detail=False, methods=['post'])
    def logout(self, request):
        return Response({"message": "Logged out successfully"})
