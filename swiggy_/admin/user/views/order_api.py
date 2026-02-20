from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from admin.delivery.models.orders import Orders
from admin.delivery.models.order_item import OrderItem
from admin.restaurants.models.cart import Cart
from admin.restaurants.models.cart_item import CartItem
from admin.user.serializers import OrderSerializer
from django.db import transaction
from admin.restaurants.models.coupon import Coupon
from django.utils import timezone as django_timezone
from django.utils import timezone
from rest_framework.pagination import CursorPagination
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def place_order_api(request):
    try:
        from admin.access.models import Users, Address
        from admin.user.serializers import PlaceOrderInputSerializer
        from decimal import Decimal
    except ImportError:
        pass

    # Admins cannot place orders for themselves (no cart)
    if getattr(request.user, 'role', None) == 'SUPERADMIN' and not isinstance(request.user, Users):
         return Response({"error": "Admins cannot place orders directly via this endpoint"}, status=status.HTTP_400_BAD_REQUEST)
         
    if not isinstance(request.user, Users):
         return Response({"error": "Valid User account required"}, status=status.HTTP_400_BAD_REQUEST)

    # 1. Validate Input
    input_serializer = PlaceOrderInputSerializer(data=request.data)
    if not input_serializer.is_valid():
        return Response({
            "error": "Invalid Input",
            "details": input_serializer.errors,
            "required_fields": ["address_id"],
             "optional_fields": ["cutlery_needed", "customer_instructions", "coupon_id", "delivery_type", "payment_method"]
        }, status=status.HTTP_400_BAD_REQUEST)
        
    data = input_serializer.validated_data
    address_id = data['address_id']
    cutlery_needed = data.get('cutlery_needed', False)
    customer_instructions = data.get('customer_instructions', '')
    coupon_id = data.get('coupon_id')
    delivery_type = data.get('delivery_type', 'Standard')
    payment_method = data.get('payment_method', 'Pay On Delivery')

    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        
        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
            
        # 2. Validate Restaurant
        restaurant = cart.restaurant
        if not restaurant.is_active:
             return Response({"error": "Restaurant is currently inactive"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not restaurant.is_open:
             return Response({"error": "Restaurant is closed"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Validate Address ownership
        try:
            address = Address.objects.get(id=address_id, user=request.user)
        except Address.DoesNotExist:
             return Response({"error": "Address not found or does not belong to user"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # 3. Validate Item Availability & Calculate Total
            item_total = Decimal('0.00')
            for item in cart_items:
                if not item.food_item.is_available:
                     return Response({"error": f"Item '{item.food_item.name}' is currently unavailable"}, status=status.HTTP_400_BAD_REQUEST)
                # item.food_item.price is the current DB price
                item_total += item.food_item.price * item.quantity
            
            # 4. Apply Coupon
            discount_amount = Decimal('0.00')
            coupon_code_str = None
            
            if coupon_id:
                try:
                    
                    coupon = Coupon.objects.filter(
                        id=coupon_id, 
                        is_active=True, 
                        expiry_date__gte=django_timezone.now().date()
                    ).first()
                    
                    if coupon:
                        coupon_code_str = coupon.code
                        if coupon.restaurant and coupon.restaurant != cart.restaurant:
                             return Response({"error": "Coupon not valid for this restaurant"}, status=status.HTTP_400_BAD_REQUEST)
                             
                        if item_total >= coupon.min_order_value:
                            if coupon.discount_type == 'Percentage':
                                discount_amount = item_total * (coupon.discount_value / 100)
                                if coupon.max_discount_amount:
                                    discount_amount = min(discount_amount, coupon.max_discount_amount)
                            else: # Flat
                                discount_amount = coupon.discount_value
                        else:
                             return Response({"error": f"Minimum order value for this coupon is {coupon.min_order_value}"}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                         return Response({"error": "Invalid or expired coupon"}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    return Response({"error": f"Coupon error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

            # 5. Delivery Fee
            delivery_fee = Decimal('30.00')
            if delivery_type == 'Express':
                delivery_fee = Decimal('50.00')
            elif delivery_type == 'Eco Saver':
                delivery_fee = Decimal('20.00')
                
            # 6. Charges
            packing_charges = Decimal('20.00')
            gst = item_total * Decimal('0.05')
            
            total_amount = item_total + gst + packing_charges + delivery_fee - discount_amount
            
            # 7. Create Order
            # Determine initial status
            initial_status = 'PENDING'
            if payment_method == 'Pay On Delivery':
                initial_status = 'ACCEPTED'

            order = Orders.objects.create(
                user=request.user,
                restaurant=cart.restaurant,
                address=address,
                subtotal=item_total,
                discount_amount=discount_amount,
                delivery_fee=delivery_fee,
                total_amount=total_amount,
                order_status=initial_status,
                payment_status='PENDING',
                customer_instructions=customer_instructions,
                cutlery_needed=cutlery_needed,
                delivery_type=delivery_type,
                coupon_code=coupon_code_str
            )
            
            # 8. Create Order Items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    food_item=cart_item.food_item,
                    food_name=cart_item.food_item.name,
                    food_image=cart_item.food_item.food_image,
                    quantity=cart_item.quantity,
                    price=cart_item.food_item.price
                )
            
            # 9. Generate OTP
            import random
            otp = str(random.randint(100000, 999999))
            order.handover_otp = otp
            order.save()
            
            # 10. Payment & Response Handling
            response_payload = {}
            
            if payment_method == 'Pay On Delivery':
                from admin.delivery.models.payment import Payment
                Payment.objects.create(
                    order=order,
                    payment_method='Pay On Delivery',
                    payment_status='PENDING',
                    amount=total_amount
                )
                response_payload = {
                    "order_id": order.id,
                    "status": "ACCEPTED"
                }

            else: # ONLINE
                # Create Payment Record for tracking
                from admin.delivery.models.payment import Payment
                from django.urls import reverse
                
                Payment.objects.create(
                    order=order,
                    payment_method=payment_method,
                    payment_status='PENDING',
                    amount=total_amount
                )
                
                # URL to initiate payment (Frontend should POST to this with order_id)
                payment_url = request.build_absolute_uri(reverse('user_payment_initiate'))
                
                response_payload = {
                    "order_id": order.id,
                    "status": "PENDING",
                    "payment_url": payment_url
                }
            
            # Clear Cart
            cart_items.delete()
            cart.restaurant = None
            cart.save()
            
            # Notifications (Mock)
            # send_notification(user, "Order Placed")
            
            return Response(response_payload, status=status.HTTP_201_CREATED)
            
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
        
    paginator = CursorPagination()
    # Ensure page size is set if not default
    paginator.page_size = 10 
    paginator.ordering = '-created_at' 
    
    # paginate_queryset returns the list of items for the page
    result_page = paginator.paginate_queryset(orders, request)
    
    # Serializer should be instantiated with the result_page (list of model instances)
    serializer = OrderSerializer(result_page, many=True)
    
    # get_paginated_response uses internal state set by paginate_queryset
    return paginator.get_paginated_response(serializer.data)
