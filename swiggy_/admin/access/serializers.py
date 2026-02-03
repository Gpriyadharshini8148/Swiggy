from rest_framework import serializers
from .models import UserAuth

class UserAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAuth
        fields = '__all__'
class VerifyOtpSerializer(serializers.Serializer):
    contact = serializers.CharField(max_length=100, help_text="Email or Phone Number")
    otp = serializers.CharField(max_length=6)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=15, required=False)
    password = serializers.CharField(max_length=128, write_only=True)

class UnifiedLoginSerializer(serializers.Serializer):
    contact = serializers.CharField(max_length=100, help_text="Email or Phone Number")
    password = serializers.CharField(max_length=128, required=False)

class SignupSerializer(serializers.Serializer):
    contact = serializers.CharField(max_length=100, help_text="Email or Phone Number")
    password = serializers.CharField(max_length=128, required=True)