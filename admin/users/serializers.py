from rest_framework import serializers
from .models import Users, Address, Wishlist, Rewards

class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model=Users
        fields='__all__'
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model=Address
        fields='__all__'
class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model=Wishlist
        fields='__all__'
class RewardsSerializer(serializers.ModelSerializer):
    class Meta:
        model=Rewards
        fields='__all__'
