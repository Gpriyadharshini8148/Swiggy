from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import UserAuth
from admin.users.models import Users
from .serializers import UserAuthSerializer, SendOtpSerializer, VerifyOtpSerializer
from django.core.mail import send_mail
import random
from drf_yasg.utils import swagger_auto_schema

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
            return Response({"error":"Email or phone number is required"}, status=status.HTTP_400_BAD_REQUEST)
        user = None
        if email:
            user = Users.objects.filter(email=email).first()
            if not user:
                user = Users.objects.create(email=email, name=email.split('@')[0], role='USER')
        elif phone:
            user = Users.objects.filter(phone=phone).first()
            if not user:
                if not phone.strip():
                     return Response({"error": "Phone number cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)
                user = Users.objects.create(phone=phone, name=f"User{phone}", role='USER')
        otp = str(random.randint(1000, 9999))
        auth_record, created = UserAuth.objects.get_or_create(user=user)
        auth_record.otp = otp
        auth_record.save()
        if email:
            try:
                send_mail('Your Swiggy Login OTP',f'Your OTP is: {otp}','noreply@swiggy.local',[email],fail_silently=False,)
            except Exception as e:
                print(f"Failed to send email: {e}")
        return Response({"message": "OTP sent successfully", "user_id": user.id,"is_new_user": False})
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
                 request.session['user_id'] = user.id
                 request.session['role'] = user.role
                 return Response({"message": "Login Successful","role": user.role,"user_id": user.id})
            else:
                return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        except UserAuth.DoesNotExist:
            return Response({"error": "OTP request not found"}, status=status.HTTP_400_BAD_REQUEST)
    @action(detail=False, methods=['post'])
    def logout(self, request):
        if 'user_id' in request.session:
            del request.session['user_id']
        if 'role' in request.session:
            del request.session['role']
        return Response({"message": "Logged out successfully"})
