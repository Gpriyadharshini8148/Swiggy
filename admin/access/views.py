from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import UserAuth
from admin.users.models import Users
from .serializers import UserAuthSerializer
class AuthViewSet(viewsets.GenericViewSet):
    queryset = UserAuth.objects.all()
    serializer_class = UserAuthSerializer
    @action(detail=False, methods=['post'])
    def send_otp(self, request):
        data = request.data
        email = data.get('email')
        phone = data.get('phone')
        
        if not email and not phone:
            return Response({"error": "Email or Phone required"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = None
        if email:
            user = Users.objects.filter(email=email).first()
            if not user:
                user = Users.objects.create(email=email, name=email.split('@')[0], role='USER')
        elif phone:
            user = Users.objects.filter(phone=phone).first()
            if not user:
                user = Users.objects.create(phone=phone, name=f"User{phone}", role='USER')
        
        otp = "1234"
        auth_record, created = UserAuth.objects.get_or_create(user=user)
        auth_record.otp = otp
        auth_record.save()
        
        return Response({
            "message": "OTP sent successfully (Sample: 1234)", 
            "user_id": user.id,
            "is_new_user": False
        })

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
                 return Response({
                     "message": "Login Successful",
                     "role": user.role,
                     "user_id": user.id
                 })
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
