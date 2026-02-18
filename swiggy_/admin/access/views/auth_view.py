from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.urls import reverse
from django.db.models import Q
from admin.restaurants.models.restaurant import Restaurant
from admin.delivery.models.delivery_partner import DeliveryPartner
from admin.access.models import Users, City, State
from admin.access.serializers import (
    VerifyOtpSerializer, LoginSerializer, UnifiedLoginSerializer, 
    SignupSerializer, LogoutSerializer, CreateAccountSerializer, 
    UsersSerializer, RestaurantSignupSerializer
)
from admin.access.permissions import IsSuperAdmin, IsAdmin
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
from django.core.cache import cache
from django.core import signing
from admin.access.signals import otp_generated, account_acceptance_email, restaurant_request_email, delivery_request_email
from admin.access.utils import executor
import re

class AuthViewSet(viewsets.GenericViewSet):
    queryset = Users.objects.all()
    serializer_class = UsersSerializer
    @swagger_auto_schema(request_body=VerifyOtpSerializer)
    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data.get('username')
        if '@' in username:
            username = username.lower()
            
        otp = serializer.validated_data.get('otp')
        cached_data = cache.get(f"signup_pending_{username}")
        if cached_data:
            if str(cached_data.get('otp')) != str(otp):
                 return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
            
            email = cached_data.get('email')
            phone = cached_data.get('phone')
            query = Q()
            if email:
                query |= Q(email=email)
            if phone:
                query |= Q(phone=phone)

            if query and Users.objects.filter(query).exists():
                 return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                user = Users.objects.create(
                    email=email,
                    phone=phone,
                    username=email.split('@')[0] if email else f"User{phone}",
                    role='USER',
                    password_hash=cached_data.get('password'),
                    is_verified=True
                )
                cache.delete(f"signup_pending_{username}")
                return Response({
                    "message": "User verified and created successfully",
                    "role": user.role,
                    "user_id": user.id,
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.validated_data.get('user')
        if not user:
             return Response({"error": "User not found or OTP expired"}, status=status.HTTP_400_BAD_REQUEST)
             
        try:
            if user.otp != otp:
                 return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
            
            user.is_verified = True
            user.save()
            return Response({
                "message": "OTP verified successfully",
                "role": user.role,
                "user_id": user.id,
            })
        except Exception as e:
             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=UnifiedLoginSerializer)
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = UnifiedLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']

        try:
            if getattr(user, 'role', '') == 'SUPERADMIN' and not isinstance(user, Users):
                 pass 
            else:
                if not user.is_verified:
                    return Response({"error": "Account not verified. Please verify your OTP to approve your account."}, status=status.HTTP_403_FORBIDDEN)

                # Prevent re-login if already logged in
                if user.is_logged_in:
                     return Response({"error": "User already logged in"}, status=status.HTTP_400_BAD_REQUEST)
                
                user.is_logged_in = True
                user.save()
        except Users.DoesNotExist:
             pass
        except Exception:
             pass

        tokens = get_tokens_for_user(user)
        
        return Response({
            "message": "Login Successful",
            "role": user.role,
            "user_id": user.id,
            "access_token": tokens['access_token'],
            "refresh_token": tokens['refresh_token']
        })
             
    @swagger_auto_schema(methods=['post'], request_body=SignupSerializer)
    @action(detail=False, methods=['post'], url_path='signup')
    def signup(self, request):
        username = request.data.get('username') or request.data.get('email') or request.data.get('phone')
        password = request.data.get('password')
        
        if not username or not password:
             return Response({"error": "Required fields missing"}, status=400)

        # 1. Fast Format Normalization & Validation (micro-seconds)
        email = None
        phone = None
        if '@' in username:
            email = username.lower()
            username = email
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                return Response({"error": "Invalid email"}, status=400)
        else:
            phone = username 
            if not phone.isdigit():
                 return Response({"error": "Invalid phone"}, status=400)

        # 2. Fast Password Complexity Check (Regex only, bypass django validators on main thread)
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password):
             return Response({"error": "enter your pass word with requird format"}, status=400)

        # 3. Fast Rate Limit Check (from cache)
        if cache.get(f"signup_pending_{username}"):
             return Response({"error": "OTP active. Wait 5 min"}, status=400)

        otp = str(random.randint(100000, 999999))
        print(f"DEBUG OTP: {otp}")

        def background_signup_task(u_name, u_email, u_phone, u_pw, u_otp):
            try:
                # 1. Background Duplication Check (Slow: DB Query)
                query = Q()
                if u_email: query |= Q(email=u_email)
                if u_phone: query |= Q(phone=u_phone)
                
                if query and Users.objects.filter(query).exists():
                    print(f"User already exists: {u_name}. Exiting background task.")
                    return

                # 2. Expensive Hashing (300-600ms)
                hashed_pw = make_password(u_pw) if u_pw else None
                
                signup_data = {
                    'email': u_email,
                    'phone': u_phone,
                    'password': hashed_pw,
                    'otp': u_otp,
                    'timestamp': str(datetime.now())
                }
                # 3. Expensive Cache write
                cache.set(f"signup_pending_{u_name}", signup_data, timeout=600)

                # 4. External Communication
                if u_email:
                    print(f"Attempting to send email to: {u_email}")
                    otp_generated.send(sender=AuthViewSet, email=u_email, otp=u_otp)
                elif u_phone:
                    try:
                        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                        client.messages.create(
                            body=f'Your Swiggy Signup OTP is: {u_otp}',
                            from_=settings.TWILIO_PHONE_NUMBER,
                            to=u_phone
                        )
                    except Exception as e:
                        print(f"Failed to send SMS: {e}")
            except Exception as e:
                print(f"Background Signup failed: {e}")

        # Submit to thread pool and return instantly
        executor.submit(background_signup_task, username, email, phone, password, otp)

        return Response({
            "message": "OTP sent for verification.", 
            "username": username,
            "is_otp_sent": True
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=LogoutSerializer)
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def logout(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data.get('user')
            if user:
                user.is_logged_in = False
                user.save()
                django_logout(request)
                return Response({"message": "Logout Successful."}, status=status.HTTP_200_OK)
            
            # Handle admin logout if needed (though typically stateless)
            admin_user = serializer.validated_data.get('admin_user')
            if admin_user:
                 django_logout(request)
                 return Response({"message": "Admin Logout Successful."}, status=status.HTTP_200_OK)
                 
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=CreateAccountSerializer)
    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    def create_account_by_super_admin(self, request):
        serializer = CreateAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        creator = None
        if request.user and request.user.is_authenticated:
            creator = request.user
        
        if not creator:
             return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
             
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        role = serializer.validated_data['role']
        admin_type = serializer.validated_data.get('admin_type', 'NONE')
        # Role-based creation restrictions
        # Safely access role, default to '' if not present 
        creator_role = getattr(creator, 'role', '')
        
        if creator_role == 'SUPER_ADMIN':
            # Super Admin has no restrictions
            pass
        elif creator_role == 'ADMIN':
            if creator.admin_type == 'RESTAURANT_ADMIN':
                # Admins can only create users within their own admin_type
                if admin_type != 'NONE' and admin_type != creator.admin_type:
                     return Response({"error": f"As a {creator.admin_type}, you can only create users with admin_type '{creator.admin_type}' or 'NONE'."}, status=status.HTTP_403_FORBIDDEN)
                
                # If they create an ADMIN role, it must match their admin_type
                if role == 'ADMIN' and admin_type != creator.admin_type:
                     return Response({"error": "Admin role must be paired with your specific admin_type."}, status=status.HTTP_403_FORBIDDEN)
                
                # Automatically set admin_type if not provided but role is ADMIN
                if role == 'ADMIN' and admin_type == 'NONE':
                    admin_type = creator.admin_type
            else:
                 return Response({"error": "Your admin account does not have permission to create users."}, status=status.HTTP_403_FORBIDDEN)

        
        email = None
        phone = None
        if '@' in username:
            email = username.lower()
        else:
            phone = username
        query = Q()
        if email:
            query |= Q(email=email)
        if phone:
            query |= Q(phone=phone)

        if query and Users.objects.filter(query).exists():
             return Response({"error": "User with this email/phone already exists"}, status=status.HTTP_400_BAD_REQUEST)
        user_data = {
            'email': email,
            'phone': phone,
            'name': email.split('@')[0] if email else f"User{phone}",
            'role': role,            'password_hash': make_password(password),
            'created_by': creator.username
        }
        # Sign and dump the data into a token
        token = signing.dumps(user_data)
        
        approve_link = f"{request.scheme}://{request.get_host()}/auth/account_creation_by_super_admin/approve_account/?token={token}"
        reject_link = f"{request.scheme}://{request.get_host()}/auth/account_creation_by_super_admin/reject_account/?token={token}"

        print(f"DEBUG APPROVE LINK: {approve_link}")
        print(f"DEBUG REJECT LINK: {reject_link}")

        if email:
            try:
                account_acceptance_email.send(
                    sender=self.__class__, 
                    email=email, 
                    password=password, 
                    approve_link=approve_link, 
                    reject_link=reject_link,
                    phone=phone,
                    role=role
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

        return Response({"message": "Account setup initiated. Approval links sent to user. Account will be created upon approval.",}, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=CreateAccountSerializer)
    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    def create_account_by_admin(self, request):
        """
        Special endpoint for Admins to create regular users only.
        Prohibits creating other Admins.
        """
        serializer = CreateAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        creator = request.user
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        role = serializer.validated_data['role']
        
        # Strict restriction: No Admin creation via this endpoint
        if role != 'USER':
             return Response({"error": "Admins using this endpoint can only create regular 'USER' roles. Admin creation is prohibited here."}, status=status.HTTP_403_FORBIDDEN)

        admin_type = 'NONE'
        
        email = None
        phone = None
        if '@' in username:
            email = username.lower()
        else:
            phone = username
            
        query = Q()
        if email: query |= Q(email=email)
        if phone: query |= Q(phone=phone)

        if query and Users.objects.filter(query).exists():
             return Response({"error": "User with this email/phone already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        user_data = {
            'email': email,
            'phone': phone,
            'name': email.split('@')[0] if email else f"User{phone}",
            'role': 'USER',
            'role': 'USER',
            # 'admin_type': 'NONE' removed
            'password_hash': make_password(password),
            'created_by': creator.username
        }
        
        token = signing.dumps(user_data)
        approve_link = f"{request.scheme}://{request.get_host()}/auth/account_creation_by_super_admin/approve_account/?token={token}"
        reject_link = f"{request.scheme}://{request.get_host()}/auth/account_creation_by_super_admin/reject_account/?token={token}"

        if email:
            try:
                account_acceptance_email.send(
                    sender=self.__class__, 
                    email=email, password=password, 
                    approve_link=approve_link, reject_link=reject_link,
                    phone=phone, role='USER'
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

        return Response({"message": "Staff/User account setup initiated. Approval links sent to user."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], authentication_classes=[])
    def approve_account(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_data = signing.loads(token, max_age=172800)
            query = Q()
            if user_data.get('email'):
                query |= Q(email=user_data['email'])
            if user_data.get('phone'):
                query |= Q(phone=user_data['phone'])

            if query and Users.objects.filter(query).exists():
                 return Response({"message": "Account already registered or verified."}, status=status.HTTP_200_OK)

            # Store in cache instead of DB
            username = user_data.get('email') or user_data.get('phone')
            activation_data = {
                'type': 'account',
                'data': user_data
            }
            cache.set(f"approved_activation_{username}", activation_data, timeout=259200) # 3 days
            
            return Response({"message": "Account Approval confirmed. Please log in with your credentials to activate your account."}, status=status.HTTP_200_OK)
            
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
        try:
            signing.loads(token, max_age=172800)
            return Response({"message": "Request Rejected. No account was created."}, status=status.HTTP_200_OK)
            
        except signing.SignatureExpired:
             return Response({"error": "Link has expired"}, status=status.HTTP_400_BAD_REQUEST)
        except signing.BadSignature:
             return Response({"error": "Invalid link"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=RestaurantSignupSerializer)
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny], authentication_classes=[])
    def restaurant_signup(self, request):
        serializer = RestaurantSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        restaurant_name = serializer.validated_data['restaurant_name']
        location = serializer.validated_data['location']
        address = serializer.validated_data.get('address')
        city_id = serializer.validated_data['city_id']
        state_id = serializer.validated_data.get('state_id')
        category = serializer.validated_data.get('category')
        
        email = None
        phone = None
        if '@' in username:
            email = username
        else:
            phone = username
            
        verification_data = {
            'email': email,
            'phone': phone,
            'password_hash': make_password(password),
            'restaurant_name': restaurant_name,
            'location': location,
            'address': address,
            'city_id': city_id,
            'state_id': state_id,
            'category': category
        }
        
        
        # Super Admin retrieval
        super_admin = Users.objects.filter(role='SUPERADMIN').first()
        super_admin_email = None
        
        if super_admin and super_admin.email:
            super_admin_email = super_admin.email
        else:
            # Fallback to Django Superuser
            django_superuser = AdminUser.objects.filter(is_superuser=True).first()
            if django_superuser and django_superuser.email:
                super_admin_email = django_superuser.email
            else:
                super_admin_email = settings.EMAIL_HOST_USER
                
        if not super_admin_email:
             return Response({"error": "Super Admin not configured or no email found to send request."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        token = signing.dumps(verification_data)
        approve_link = f"{request.scheme}://{request.get_host()}/auth/account_creation_by_super_admin/approve_restaurant/?token={token}"
        reject_link = f"{request.scheme}://{request.get_host()}/auth/account_creation_by_super_admin/reject_restaurant/?token={token}"
        
        restaurant_request_email.send(
            sender=self.__class__, 
            super_admin_email=super_admin_email, 
            restaurant_name=restaurant_name, 
            approve_link=approve_link, 
            reject_link=reject_link
        )
        
        return Response({"message": "Restaurant signup request sent to Super Admin for approval."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], authentication_classes=[])
    def approve_restaurant(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            data = signing.loads(token, max_age=259200) # 3 days validity
            
            # Check if user already exists
            query = Q()
            if data.get('email'):
                query |= Q(email=data['email'])
            if data.get('phone'):
                query |= Q(phone=data['phone'])
                
            if query and Users.objects.filter(query).exists():
                 return Response({"message": "User for this restaurant already exists."}, status=status.HTTP_200_OK)

            # Store in cache instead of DB
            username = data.get('email') or data.get('phone')
            activation_data = {
                'type': 'restaurant',
                'data': data
            }
            cache.set(f"approved_activation_{username}", activation_data, timeout=259200)
            
            return Response({"message": f"Restaurant '{data['restaurant_name']}' approved. The admin can now log in to activate the account and restaurant profile."}, status=status.HTTP_200_OK)
            
        except signing.SignatureExpired:
             return Response({"error": "Link has expired"}, status=status.HTTP_400_BAD_REQUEST)
        except signing.BadSignature:
             return Response({"error": "Invalid link"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
             return Response({"error": f"Approval failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], authentication_classes=[])
    def reject_restaurant(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            data = signing.loads(token, max_age=259200)
            return Response({"message": f"Restaurant request for '{data['restaurant_name']}' has been rejected."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Invalid or expired link"}, status=status.HTTP_400_BAD_REQUEST)


