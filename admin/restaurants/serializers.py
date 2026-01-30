from rest_framework import serializers
from .models import Restaurant, Category, FoodItem, Cart, CartItem, Coupon, Customization

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=Category
        fields='__all__'
class CustomizationSerializer(serializers.ModelSerializer):
    class Meta:
        model=Customization
        fields='__all__'
class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model=Restaurant
        fields='__all__'
class FoodItemSerializer(serializers.ModelSerializer):
    class Meta:
        model=FoodItem
        fields='__all__'
class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model=CartItem
        fields='__all__'
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cartitem_set', many=True, read_only=True)
    class Meta:
        model=Cart
        fields='__all__'
class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model=Coupon
        fields='__all__'
