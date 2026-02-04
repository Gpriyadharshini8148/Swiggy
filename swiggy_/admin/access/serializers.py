from rest_framework import serializers
from .models import UserAuth
from admin.users.models import Users
from django.contrib.auth.models import User as AdminUser
from django.contrib.auth.hashers import check_password
from admin.users.models import Users
from django.contrib.auth.models import User as AdminUser
class UserAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAuth
        fields = '__all__'
class VerifyOtpSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100, help_text="Email or Phone Number")
    otp = serializers.CharField(max_length=6)
    def validate(self, attrs):
        from admin.users.models import Users
        username = attrs.get('username')
        otp = attrs.get('otp')
        user = None
        if '@' in username:
             user = Users.objects.filter(email=username).first()
        else:
             user = Users.objects.filter(phone=username).first()
        
        if not user:
            raise serializers.ValidationError({"username": "User not found for provided username"})
            
        try:
            auth_record = UserAuth.objects.get(user=user)
            if auth_record.otp != otp:
                raise serializers.ValidationError({"otp": "Invalid OTP"})
        except UserAuth.DoesNotExist:
             raise serializers.ValidationError("OTP request not found")
        
        attrs['user'] = user
        return attrs

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=15, required=False)
    password = serializers.CharField(max_length=128, write_only=True)

class UnifiedLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100, help_text="Email or Phone Number")
    password = serializers.CharField(max_length=128)

    def validate(self, attrs):
        from admin.users.models import Users
        from django.contrib.auth.hashers import check_password
        username = attrs.get('username')
        password = attrs.get('password')
        
        user = None
        if '@' in username:
            user = Users.objects.filter(email=username).first()
        else:
            user = Users.objects.filter(phone=username).first()
            
        if not user:
             raise serializers.ValidationError("User not found")
             
        if user.password_hash and check_password(password, user.password_hash):
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError("Invalid Password")

class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100, help_text="Email or Phone Number")
    password = serializers.CharField(max_length=128, required=True)

    def validate(self, data):
        from admin.users.models import Users
        username = data.get('username')
        if not username:
             raise serializers.ValidationError("Username is required")

        email = None
        phone = None
        
        if '@' in username:
            email = username
        else:
            phone = username
            
        if email and Users.objects.filter(email=email).exists():
            raise serializers.ValidationError("User with this email already exists")
            
        if phone and Users.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("User with this phone already exists")
            
        return data

class LogoutSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100, help_text="Email or Phone Number")
    def validate(self, attrs):
        username = attrs.get('username')
        user = None
        admin_user = None 
        if '@' in username:
            user = Users.objects.filter(email=username).first()
        else:
            user = Users.objects.filter(phone=username).first()
        if not user and '@' in username:
             admin_user = AdminUser.objects.filter(email=username).first()
        if not user and not admin_user:
            raise serializers.ValidationError("User not found")
            
        attrs['user'] = user
        attrs['admin_user'] = admin_user
        return attrs