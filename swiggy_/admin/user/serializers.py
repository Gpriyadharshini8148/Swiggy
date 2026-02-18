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
from admin.access.models.wishlist import Wishlist
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
        fields = ['id', 'name', 'image']

class RestaurantListSerializer(serializers.ModelSerializer):
    time_taken_for_delivery = serializers.SerializerMethodField()
    restaurant_location = serializers.SerializerMethodField()
    offers = serializers.SerializerMethodField()
    veg_or_non_veg = serializers.SerializerMethodField()
    outlets = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'logo_image', 'banner_image', 'rating', 'restaurant_location', 'time_taken_for_delivery', 'offers', 'veg_or_non_veg', 'outlets']
    
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
             # Fallback if no location data: Return estimate based on city average? Or just N/A
            return "30-40 mins" # Default fallback for now if location fails
        
        try:
            # Step A: Calculate Distance (Haversine Formula)
            # Ensure coordinates are floats
            u_lat = float(user_lat)
            u_lng = float(user_lng)
            
            # Check if restaurant location is valid point
            if not obj.location or not hasattr(obj.location, 'x') or not hasattr(obj.location, 'y'):
                 return "30-40 mins"

            r_lat = obj.location.y
            r_lng = obj.location.x

            lon1, lat1, lon2, lat2 = map(radians, [u_lng, u_lat, r_lng, r_lat])
            dlon = lon2 - lon1 
            dlat = lat2 - lat1 
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a)) 
            r = 6371 # Radius of earth in kilometers
            distance_km = c * r
            
            # 1. Restaurant Preparation Time
            prep_time = 20 # minutes (average)
            
            # 2. Rider Assignment Time
            assignment_buffer = 5 # minutes
            
            # 3. Travel Time Calculation
            # Average speed in city: 25 km/hr
            avg_speed_kmph = 25
            travel_time_mins = (distance_km / avg_speed_kmph) * 60
            
            # 4. Buffer Time (Traffic, rain, parking, etc)
            buffer_time = 5 # minutes
            
            # Final ETA
            total_time_mins = int(prep_time + assignment_buffer + travel_time_mins + buffer_time)
            
            # Show a range
            lower_bound = total_time_mins - 2
            upper_bound = total_time_mins + 3
            
            return f"{lower_bound}-{upper_bound} mins"
        except Exception as e:
            print(f"DEBUG ETA ERROR: {e}")
            return "35-45 mins" # Falback on error

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
    cart_added = serializers.SerializerMethodField()
    wishlist_added = serializers.SerializerMethodField()
    ratings = serializers.DecimalField(source='rating', max_digits=3, decimal_places=1, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    sub_category_name = serializers.CharField(source='sub_category.name', read_only=True)
    banner_image = serializers.ImageField(source='restaurant.banner_image', read_only=True)
    logo_image = serializers.ImageField(source='restaurant.logo_image', read_only=True)

    class Meta:
        model = FoodItem
        fields = ['id', 'restaurant', 'category', 'category_name', 'sub_category', 'sub_category_name', 'name', 'food_image', 'description', 'ratings', 'customization', 'price', 'discount_type', 'discount_value', 'discounted_price', 'is_available', 'is_veg', 'is_both', 'cart', 'cart_added', 'wishlist_added', 'banner_image', 'logo_image']


    def get_cart_added(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.is_authenticated:
            try:
                # Optimized to just check existence
                # We need to filter by user. 
                # Assuming standard Cart model structure where one user has one cart
                cart = Cart.objects.filter(user=user).first()
                if cart:
                    return CartItem.objects.filter(cart=cart, food_item=obj).exists()
            except Exception:
                pass
        return False

    def get_wishlist_added(self, obj):
        from admin.access.models.wishlist import Wishlist
        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.is_authenticated:
            try:
                # Check for active wishlist item (not soft deleted)
                return Wishlist.objects.filter(user=user, food_item=obj, deleted_at__isnull=True).exists()
            except Exception:
                pass
        return False

    def get_cart(self, obj):
        # Returns current quantity in cart
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
class WishlistSerializer(serializers.ModelSerializer):
    food_item_details = FoodItemSerializer(source='food_item', read_only=True)
    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'food_item', 'food_item_details', 'created_at']
        read_only_fields = ['user', 'created_at']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'image']



class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'food_item', 'food_name', 'food_image', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True, source='orderitem_set')
    class Meta:
        model = Orders
        fields = ['id', 'user', 'restaurant', 'items', 'address', 'subtotal', 'discount_amount', 'delivery_fee', 'total_amount', 'order_status', 'payment_status', 'customer_instructions', 'cutlery_needed', 'delivery_type', 'coupon_code', 'created_at']

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
        fields = ['username', 'phone', 'email', 'profile_image', 'addresses', 'payment_methods', 'refunds', 'past_orders']

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

class PlaceOrderInputSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(required=True)
    cutlery_needed = serializers.BooleanField(required=False, default=False)
    customer_instructions = serializers.CharField(required=False, allow_blank=True)
    coupon_id = serializers.IntegerField(required=False, allow_null=True)
    delivery_type = serializers.ChoiceField(choices=['Standard', 'Express', 'Eco Saver'], default='Standard')
    payment_method = serializers.ChoiceField(choices=['Pay On Delivery', 'UPI', 'Card', 'Wallet'], default='Pay On Delivery')
