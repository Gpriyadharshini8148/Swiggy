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
        from admin.access.models import Users
    except ImportError:
        pass

    # Admins cannot place orders for themselves (no cart)
    if getattr(request.user, 'role', None) == 'SUPERADMIN' and not isinstance(request.user, Users):
         return Response({"error": "Admins cannot place orders directly via this endpoint"}, status=status.HTTP_400_BAD_REQUEST)
         
    if not isinstance(request.user, Users):
         return Response({"error": "Valid User account required"}, status=status.HTTP_400_BAD_REQUEST)

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
                order_status='PENDING',
                payment_status='PENDING'
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
        from admin.access.models import Users
    except ImportError:
        pass
        
    try:
        if getattr(request.user, 'role', None) == 'SUPERADMIN' or getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False):
            order = Orders.objects.get(id=order_id)
        elif isinstance(request.user, Users):
            order = Orders.objects.get(id=order_id, user=request.user)
        else:
             return Response({"error": "Valid User/User ID required for order access"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "order_id": order.id,
            "status": order.order_status,
            "payment_status": order.payment_status,
            "delivery_partner": None, # order.delivery_partner field does not exist yet
        })
    except Orders.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_user_orders_api(request):
    try:
        from admin.access.models import Users
    except ImportError:
        pass

    if getattr(request.user, 'role', None) == 'SUPERADMIN' or getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False):
        orders = Orders.objects.all().order_by('-created_at')
    elif isinstance(request.user, Users):
        orders = Orders.objects.filter(user=request.user).order_by('-created_at')
    else:
        return Response({"error": "Valid User/User ID required for order access"}, status=status.HTTP_400_BAD_REQUEST)
        
    return Response(OrderSerializer(orders, many=True).data)
