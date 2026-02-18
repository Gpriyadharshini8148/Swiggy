from rest_framework import serializers
from .models import Restaurant, Category, SubCategory, FoodItem, Cart, CartItem, Coupon, Customization
from admin.access.models import Users
from admin.delivery.models.orders import Orders
from admin.restaurants.models.review import Review
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=Category
        fields=['id', 'name', 'image']
class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=SubCategory
        fields=['id', 'category', 'name', 'image']
class CustomizationSerializer(serializers.ModelSerializer):
    class Meta:
        model=Customization
        fields=['id', 'suggestions', 'number_of_ingredients']
class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model=Restaurant
        fields=['id', 'name', 'logo_image', 'banner_image', 'location', 'address', 'state', 'city', 'rating', 'category', 'user', 'opening_time', 'closing_time', 'is_verified', 'is_active']
class FoodItemSerializer(serializers.ModelSerializer):
    class Meta:
        model=FoodItem
        fields=['id', 'restaurant', 'category', 'sub_category', 'name', 'food_image', 'customization', 'price', 'discount_type', 'discount_value', 'discounted_price', 'is_available', 'is_veg', 'is_both']
class CartItemSerializer(serializers.ModelSerializer):
    food_item_id = serializers.IntegerField(source='food_item.id', read_only=True)
    restaurant_id = serializers.IntegerField(source='food_item.restaurant.id', read_only=True)
    food_name = serializers.CharField(source='food_item.name', read_only=True)
    price = serializers.DecimalField(source='food_item.price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model=CartItem
        fields=['id', 'food_item_id', 'restaurant_id', 'food_name', 'price', 'quantity']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source='cartitem_set', many=True, read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=Users.objects.all(), required=False)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model=Cart
        fields=['id', 'user', 'restaurant', 'items', 'total_amount']

    def get_total_amount(self, obj):
        return sum(item.quantity * item.food_item.price for item in obj.cartitem_set.all())

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model=Coupon
        fields=['id', 'code', 'description', 'coupon_image', 'discount_type', 'discount_value', 'max_discount_amount', 'min_order_value', 'scope', 'restaurant', 'expiry_date', 'is_active']
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
