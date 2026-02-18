from decimal import Decimal
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.delivery.models import Orders, OrderItem, Payment
from admin.delivery.serializers import OrdersSerializer
from admin.access.permissions import IsAuthenticatedUser
from admin.access.models import Users
from admin.restaurants.models import Cart
from django.db import transaction
from django.conf import settings
import razorpay
from admin.delivery.models import Delivery
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class OrdersViewSet(viewsets.ModelViewSet):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer
    permission_classes = [IsAuthenticatedUser]
    def get_queryset(self):
        user_id = None
        role = None

        if self.request.user and self.request.user.is_authenticated:
            if hasattr(self.request.user, 'role'):
                role = self.request.user.role
                user_id = self.request.user.id
            elif getattr(self.request.user, 'is_superuser', False): # Django Admin
                role = 'SUPERADMIN'
                user_id = self.request.user.id
            elif getattr(self.request.user, 'role', None) == 'SUPERADMIN': # Custom patch
                role = 'SUPERADMIN'
                user_id = self.request.user.id

        # Fallback to legacy session check
        if not user_id:
            user_id = self.request.session.get('user_id')
            if user_id:
                try:
                    user = Users.objects.get(id=user_id)
                    role = user.role
                except Users.DoesNotExist:
                     pass

        if not user_id:
            return Orders.objects.none()

        if role in ['ADMIN', 'SUPERADMIN']:
            return Orders.objects.all()
        else:
            return Orders.objects.filter(user_id=user_id)
    @action(detail=False, methods=['post'])
    def place_order(self, request):
        user = request.user
        if not (user and user.is_authenticated):
            user_id = request.session.get('user_id')
            if not user_id:
                return Response({"error": "Authentication required"}, status=401)
            try:
                user = Users.objects.get(id=user_id)
            except Users.DoesNotExist:
                return Response({"error": "User not found"}, status=401)
        elif not isinstance(user, Users):
            # If logged in user is Django User (e.g. admin), try to find corresponding custom User
            # OR prevent them from ordering if they don't have a custom User profile.
            # Assuming for now we need the custom User model for the Cart foreign key.
            try:
                
                # Sidenote: The error 'Cannot query "gpriyadharshini9965": Must be "Users" instance'
                # confirms Cart.user expects admin.access.models.Users, but we passed request.user (Django User).
                
                user = Users.objects.get(email=user.email)
            except Users.DoesNotExist:
                 # Fallback: if we can't map to a custom user, maybe we can't place an order?
                 # Or we act as if no cart exists for this identity.
                 return Response({"error": "Valid Customer User profile required to place orders."}, status=400)

        address_id = request.data.get('address_id') or request.data.get('address')
        customer_instructions = request.data.get('customer_instructions', '')

        if not address_id:
            return Response({"error": "address_id is required"}, status=400)
        
        # Get cart for the user
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
             return Response({"error": "Cart is empty (cart not found)"}, status=400)
             
        # Get cart items
        from admin.restaurants.models import CartItem
        cart_items = CartItem.objects.filter(cart=cart)
        
        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=400)
            
        # Validate that all items are from the same restaurant
        restaurant = cart.restaurant
        if not restaurant:
             # Should not happen if items exist but safety check
             restaurant = cart_items.first().food_item.restaurant
        
        # Check if restaurant is open
        if not restaurant.is_active:
             return Response({"error": "Restaurant is currently closed"}, status=400)
        
        # Calculate totals
        subtotal = sum(item.food_item.price * item.quantity for item in cart_items)
        delivery_fee = Decimal('40.00')  # Fixed delivery fee
        total_amount = subtotal + delivery_fee
        
        try:
            with transaction.atomic():
                # 1. Create Order
                order = Orders.objects.create(
                    user=user,
                    restaurant=restaurant,
                    address_id=address_id,
                    subtotal=subtotal,
                    delivery_fee=delivery_fee,
                    total_amount=total_amount,
                    order_status='PENDING',
                    payment_status='PENDING',
                    customer_instructions=customer_instructions
                )
                
                # 2. Create Order Items from Cart
                for cart_item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        food_item=cart_item.food_item,
                        food_name=cart_item.food_item.name,
                        food_image=cart_item.food_item.food_image,
                        quantity=cart_item.quantity, 
                        price=cart_item.food_item.price
                    )
                
                # 3. Clear the Cart
                cart_items.delete()
                cart.restaurant = None
                cart.save()
                
                # 4. Initiate Razorpay Order
                amount_paise = int(total_amount * 100)
                razorpay_data = {
                    "amount": amount_paise,
                    "currency": "INR",
                    "receipt": f"receipt_order_{order.id}",
                    "payment_capture": 1
                }
                
                razorpay_order = client.order.create(data=razorpay_data)
                
                # 5. Create Payment record
                Payment.objects.create(
                    order=order,
                    payment_method='razorpay',
                    razorpay_order_id=razorpay_order['id'],
                    payment_status='PENDING'
                )
                
                return Response({
                    "message": "Order placed successfully",
                    "order_id": order.id,
                    "total_amount": float(total_amount),
                    "razorpay_order_id": razorpay_order['id'],
                    "razorpay_key": settings.RAZORPAY_KEY_ID,
                    "currency": "INR"
                }, status=201)
                
        except Exception as e:
            print(f"Error placing order: {str(e)}")
            return Response({"error": f"Failed to place order: {str(e)}"}, status=400)
    @action(detail=True, methods=['post'])
    def cancel_order(self, request, pk=None):
        order = self.get_object()
        if order.order_status == 'DELIVERED':
            return Response({'message': 'You cannot cancel this order because it is already delivered'}, status=400)
        order.order_status = 'CANCELLED'
        order.save()
        return Response({'message': 'Your order has been cancelled successfully'}, status=200)
    @action(detail=True, methods=['get'])
    def track_order(self, request, pk=None):
        order = self.get_object()
        
        # Get delivery partner name via the Delivery model
      
        delivery = Delivery.objects.filter(order=order).first()
        delivery_partner_name = delivery.delivery_partner.name if delivery and delivery.delivery_partner else None
        
        return Response({
            'order_id': order.id,
            'order_status': order.order_status,
            'delivery_partner_name': delivery_partner_name
        })