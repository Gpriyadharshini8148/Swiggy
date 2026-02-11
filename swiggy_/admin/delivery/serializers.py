from rest_framework import serializers
from .models import Orders, OrderItem, Payment, Delivery, DeliveryPartner
from admin.access.models import Users
from admin.restaurants.models import Restaurant
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model=OrderItem
        fields=['id', 'order', 'food_item', 'food_name', 'food_image_url', 'quantity', 'price']

class OrdersSerializer(serializers.ModelSerializer):
    items=OrderItemSerializer(many=True, read_only=True, source='orderitem_set')
    user = serializers.CharField()
    restaurant = serializers.CharField()

    class Meta:
        model=Orders
        fields=['id', 'user', 'restaurant', 'address', 'subtotal', 'discount_amount', 'delivery_fee', 'total_amount', 'order_status', 'payment_status', 'customer_instructions', 'preparation_timestamp', 'ready_timestamp', 'pickup_timestamp', 'delivered_timestamp', 'items']

    def validate(self, attrs):
        user_input = attrs.get('user')
        if user_input:

             user_obj = Users.objects.filter(email=user_input).first() or \
                        Users.objects.filter(phone=user_input).first() or \
                        Users.objects.filter(username=user_input).first()
             
             if not user_obj:
                  if isinstance(user_input, int) or (isinstance(user_input, str) and user_input.isdigit()):
                       user_obj = Users.objects.filter(id=int(user_input)).first()
             if not user_obj:
                  raise serializers.ValidationError({"user": f"User '{user_input}' not found"})
             attrs['user'] = user_obj
        rest_input = attrs.get('restaurant')
        if rest_input:
             rest_obj = Restaurant.objects.filter(name=rest_input).first()
             if not rest_obj:
                 if isinstance(rest_input, int) or (isinstance(rest_input, str) and rest_input.isdigit()):
                       rest_obj = Restaurant.objects.filter(id=int(rest_input)).first()
                       
             if not rest_obj:
                  raise serializers.ValidationError({"restaurant": f"Restaurant '{rest_input}' not found"})
             attrs['restaurant'] = rest_obj
             
        return attrs

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model=Payment
        fields=['id', 'order', 'payment_method', 'payment_status', 'transaction_id', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'paid_at']

class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model=Delivery
        fields=['id', 'order', 'delivery_partner', 'delivery_status', 'delivered_at']

class DeliveryPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model=DeliveryPartner
        fields=['id', 'user', 'name', 'phone', 'email', 'profile_image_url', 'vehicle_type', 'vehicle_number', 'license_number', 'rating', 'total_deliveries', 'is_active', 'is_verified']