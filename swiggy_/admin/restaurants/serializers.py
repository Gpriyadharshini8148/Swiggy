from rest_framework import serializers
from .models import Restaurant, Category, SubCategory, FoodItem, Cart, CartItem, Coupon, Customization
from admin.access.models import Users
from admin.delivery.models.orders import Orders
from admin.restaurants.models.review import Review
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=Category
        fields=['id', 'name', 'image_url']
class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=SubCategory
        fields=['id', 'category', 'name', 'image_url']
class CustomizationSerializer(serializers.ModelSerializer):
    class Meta:
        model=Customization
        fields=['id', 'suggestions', 'number_of_ingredients']
class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model=Restaurant
        fields=['id', 'name', 'logo_image_url', 'banner_image_url', 'location', 'address', 'state', 'city', 'rating', 'category', 'user', 'opening_time', 'closing_time', 'is_verified', 'is_active']
class FoodItemSerializer(serializers.ModelSerializer):
    class Meta:
        model=FoodItem
        fields=['id', 'restaurant', 'category', 'sub_category', 'name', 'food_image_url', 'customization', 'price', 'discount_type', 'discount_value', 'discounted_price', 'is_available', 'is_veg', 'is_both']
class CartItemSerializer(serializers.ModelSerializer):
    food_item_details = FoodItemSerializer(source='food_item', read_only=True)
    class Meta:
        model=CartItem
        fields=['id', 'cart', 'food_item', 'quantity', 'food_item_details']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cartitem_set', many=True, read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=Users.objects.all(), required=False)
    class Meta:
        model=Cart
        fields=['id', 'user', 'restaurant', 'items']
class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model=Coupon
        fields=['id', 'code', 'description', 'coupon_image_url', 'discount_type', 'discount_value', 'max_discount_amount', 'min_order_value', 'scope', 'restaurant', 'expiry_date', 'is_active']
class RestaurantOrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='user.username', read_only=True)
    customer_phone = serializers.CharField(source='user.phone', read_only=True)
    delivery_address = serializers.SerializerMethodField()
    
    class Meta:
        model = Orders
        fields = ['id', 'customer_name', 'customer_phone', 'delivery_address', 'total_amount', 'order_status', 'payment_status', 'customer_instructions', 'created_at', 'preparation_timestamp', 'ready_timestamp', 'pickup_timestamp', 'delivered_timestamp']
        
    def get_delivery_address(self, obj):
        if obj.address:
            return f"{obj.address.street_address}, {obj.address.city.name}, {obj.address.state.name} - {obj.address.pincode}"
        return None
class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = Review
        fields = ['id', 'username', 'rating', 'comment', 'created_at']
