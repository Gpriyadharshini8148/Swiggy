from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from admin.delivery.models.orders import Orders
from admin.delivery.models.order_item import OrderItem
from admin.restaurants.models.cart import Cart
from admin.restaurants.models.cart_item import CartItem
from admin.user.serializers import OrderSerializer
from django.db import transaction

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def place_order_api(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        
        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
            
        with transaction.atomic():
            # Create Order
            # Calculate total first
            item_total = sum(item.food_item.price * item.quantity for item in cart_items)
            # Add taxes/fees (simplified)
            total_amount = float(item_total) + 50.00 # Placeholder for taxes/fees
            
            order = Orders.objects.create(
                user=request.user,
                restaurant=cart.restaurant,
                total_amount=total_amount,
                status='PENDING',
                payment_status='UNPAID'
            )
            
            # Create Order Items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    food_item=cart_item.food_item,
                    food_name=cart_item.food_item.name,
                    food_image_url=cart_item.food_item.food_image_url,
                    quantity=cart_item.quantity,
                    price=cart_item.food_item.price
                )
            
            # Clear Cart
            cart_items.delete()
            cart.restaurant = None
            cart.save()
            
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
            
    except Cart.DoesNotExist:
        return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_order_status_api(request, order_id):
    try:
        order = Orders.objects.get(id=order_id, user=request.user)
        return Response({
            "order_id": order.id,
            "status": order.status,
            "payment_status": order.payment_status,
            "delivery_partner": order.delivery_partner.username if order.delivery_partner else None
        })
    except Orders.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_user_orders_api(request):
    orders = Orders.objects.filter(user=request.user).order_by('-created_at')
    return Response(OrderSerializer(orders, many=True).data)
