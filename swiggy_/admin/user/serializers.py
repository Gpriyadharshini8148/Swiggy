from rest_framework import serializers
from admin.access.models.users import Users
from admin.access.models.address import Address
from admin.user.models.serviceable_zone import ServiceableZone
from admin.user.models.notification import Notification
from admin.restaurants.models.restaurant import Restaurant
from admin.restaurants.models.food_item import FoodItem
from admin.restaurants.models.category import Category, SubCategory
from admin.restaurants.models.cart import Cart
from admin.restaurants.models.cart_item import CartItem
from admin.delivery.models.orders import Orders
from admin.delivery.models.order_item import OrderItem
from admin.restaurants.models.review import Review

class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['username', 'phone', 'email', 'password_hash']
        extra_kwargs = {'password_hash': {'write_only': True}}

class UserLoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=17)
    otp = serializers.CharField(max_length=6, required=False)

class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'
        read_only_fields = ['user']

class ServiceableZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceableZone
        fields = '__all__'

class RestaurantListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'logo_image_url', 'rating', 'delivery_time', 'location']

class FoodItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodItem
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'



class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True, source='orderitem_set')
    class Meta:
        model = Orders
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['user']
