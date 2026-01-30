from rest_framework import serializers
from .models import Orders, OrderItem, Payment, Delivery, DeliveryPartner

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model=OrderItem
        fields='__all__'

class OrdersSerializer(serializers.ModelSerializer):
    items=OrderItemSerializer(many=True, read_only=True, source='orderitem_set')
    class Meta:
        model=Orders
        fields='__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model=Payment
        fields='__all__'

class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model=Delivery
        fields='__all__'

class DeliveryPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model=DeliveryPartner
        fields='__all__'
