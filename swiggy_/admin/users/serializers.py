from rest_framework import serializers
from .models import Users, Address, Wishlist, Rewards

class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = '__all__'
        extra_kwargs = {
            'password_hash': {'write_only': True},
            'deleted_at': {'read_only': True},
            'created_by': {'read_only': True},
            'updated_by': {'read_only': True},
            'deleted_by': {'read_only': True},
        }

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'
class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = '__all__'
class RewardsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rewards
        fields = '__all__'
