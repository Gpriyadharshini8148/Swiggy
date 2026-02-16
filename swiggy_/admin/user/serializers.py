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
from admin.restaurants.models.coupon import Coupon
from math import radians, cos, sin, asin, sqrt
from django.contrib.gis.geos import Point

class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['username', 'phone', 'email', 'password_hash']
        extra_kwargs = {'password_hash': {'write_only': True}}

class UserLoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=17)
    otp = serializers.CharField(max_length=6, required=False)

class UserAddressSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)

    class Meta:
        model = Address
        fields = ['id', 'user', 'city', 'state', 'address_line_1', 'address_line_2', 'landmark', 'pincode', 'latitude', 'longitude', 'is_default', 'address_tag']
        read_only_fields = ['user']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.location:
            ret['latitude'] = instance.location.y
            ret['longitude'] = instance.location.x
        else:
            ret['latitude'] = None
            ret['longitude'] = None
        return ret

    def create(self, validated_data):
        lat = validated_data.pop('latitude', None)
        lng = validated_data.pop('longitude', None)
        instance = super().create(validated_data)
        if lat is not None and lng is not None:
            instance.location = Point(float(lng), float(lat), srid=4326)
            instance.save()
        return instance

    def update(self, instance, validated_data):
        lat = validated_data.pop('latitude', None)
        lng = validated_data.pop('longitude', None)
        instance = super().update(instance, validated_data)
        if lat is not None and lng is not None:
             instance.location = Point(float(lng), float(lat), srid=4326)
             instance.save()
        return instance

class ServiceableZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceableZone
        fields = ['id', 'city', 'zone_name', 'center_latitude', 'center_longitude', 'radius_km', 'is_active']

class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'image_url']

class RestaurantListSerializer(serializers.ModelSerializer):
    time_taken_for_delivery = serializers.SerializerMethodField()
    restaurant_location = serializers.SerializerMethodField()
    offers = serializers.SerializerMethodField()
    veg_or_non_veg = serializers.SerializerMethodField()
    outlets = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'logo_image_url', 'banner_image_url', 'rating', 'restaurant_location', 'time_taken_for_delivery', 'offers', 'veg_or_non_veg', 'outlets']
    
    def get_time_taken_for_delivery(self, obj):
        user_lat = self.context.get('lat')
        user_lng = self.context.get('lng')
        
        # Fallback to user's default address if lat/lng not in query params
        if not user_lat or not user_lng:
            request = self.context.get('request')
            if request and request.user.is_authenticated:
                # Try to get default address using username lookup to avoid model instance mismatch
                default_address = Address.objects.filter(user__username=request.user.username, is_default=True).first()
                if not default_address:
                    # Fallback to any address
                    default_address = Address.objects.filter(user__username=request.user.username).first()
                
                if default_address and default_address.location:
                    user_lat = default_address.location.y
                    user_lng = default_address.location.x

        if not user_lat or not user_lng or not obj.location:
            return "N/A"
        
        try:
            # Simple Haversine approximation
            lon1, lat1, lon2, lat2 = map(radians, [float(user_lng), float(user_lat), obj.location.x, obj.location.y])
            dlon = lon2 - lon1 
            dlat = lat2 - lat1 
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a)) 
            r = 6371 # Radius of earth in kilometers
            distance = c * r
            
            # Avg speed 20km/h => 3 min/km. Prep time 15 min.
            time_mins = int((distance * 3) + 15)
            return f"{time_mins} mins"
        except Exception:
            return "N/A"

    def get_restaurant_location(self, obj):
        return f"{obj.address}, {obj.city.name if obj.city else ''}"

    def get_offers(self, obj):
        coupons = Coupon.objects.filter(restaurant=obj, is_active=True).values_list('code', 'discount_type', 'discount_value')
        return [f"{c[0]}: {c[1]} {c[2]}" for c in coupons]

    def get_veg_or_non_veg(self, obj):
        # Check food items
        # fetching from FoodItem which is imported
        items = FoodItem.objects.filter(restaurant=obj)
        has_veg = items.filter(is_veg=True).exists()
        has_non_veg = items.filter(is_veg=False).exists()
        
        if has_veg and has_non_veg:
            return "Both"
        elif has_veg:
            return "Veg"
        elif has_non_veg:
            return "Non-Veg"
        return "Not Specified"

    def get_outlets(self, obj):
        # Count restaurants with same name
        return Restaurant.objects.filter(name__iexact=obj.name).count()

class FoodItemSerializer(serializers.ModelSerializer):
    cart = serializers.SerializerMethodField()
    ratings = serializers.DecimalField(source='rating', max_digits=3, decimal_places=1, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    banner_image_url = serializers.CharField(source='restaurant.banner_image_url', read_only=True)
    logo_image_url = serializers.CharField(source='restaurant.logo_image_url', read_only=True)

    class Meta:
        model = FoodItem
        fields = ['id', 'restaurant', 'category', 'category_name', 'sub_category', 'name', 'food_image_url', 'description', 'ratings', 'customization', 'price', 'discount_type', 'discount_value', 'discounted_price', 'is_available', 'is_veg', 'is_both', 'cart', 'banner_image_url', 'logo_image_url']


    def get_cart(self, obj):
        # Alias for cart quantity
        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.is_authenticated:
            try:
                cart = Cart.objects.filter(user=user).first()
                if cart:
                    cart_item = CartItem.objects.filter(cart=cart, food_item=obj).first()
                    return cart_item.quantity if cart_item else 0
            except Exception:
                pass
        return 0

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'image_url']



class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'food_item', 'food_name', 'food_image_url', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True, source='orderitem_set')
    class Meta:
        model = Orders
        fields = ['id', 'user', 'restaurant', 'items', 'address', 'subtotal', 'discount_amount', 'delivery_fee', 'total_amount', 'order_status', 'payment_status', 'customer_instructions', 'created_at']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'is_read', 'notification_type', 'created_at']

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'user', 'restaurant', 'order', 'rating', 'comment', 'created_at']
        read_only_fields = ['user']

class UserProfileSerializer(serializers.ModelSerializer):
    addresses = UserAddressSerializer(many=True, read_only=True)
    past_orders = serializers.SerializerMethodField()
    refunds = serializers.SerializerMethodField()
    payment_methods = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ['username', 'phone', 'email', 'profile_image_url', 'addresses', 'payment_methods', 'refunds', 'past_orders']

    def get_past_orders(self, obj):
        orders = Orders.objects.filter(user=obj).order_by('-created_at')
        return OrderSerializer(orders, many=True).data

    def get_refunds(self, obj):
        refunds = Orders.objects.filter(user=obj, order_status='CANCELLED').order_by('-created_at')
        return OrderSerializer(refunds, many=True).data

    def get_payment_methods(self, obj):
         from admin.delivery.models.payment import Payment
         methods = Payment.objects.filter(order__user=obj).values_list('payment_method', flat=True).distinct()
         return list(methods)
