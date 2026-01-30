from rest_framework import serializers
from .models import UserAuth

class UserAuthSerializer(serializers.ModelSerializer):
    class Meta:
        model=UserAuth
        fields='__all__'

class SendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=15, required=False)

class VerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=15, required=False)
    otp = serializers.CharField(max_length=6)