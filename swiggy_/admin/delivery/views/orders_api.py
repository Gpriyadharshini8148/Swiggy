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
from django.db.models import Count, Q
from django.contrib.gis.db.models.functions import Distance
from django.conf import settings
import razorpay
from django.utils import timezone
from admin.delivery.models import Delivery, DeliveryPartner

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
        elif role in ['DELIVERY_ADMIN', 'DELIVERY_PARTNER']:
            return Orders.objects.filter(delivery__delivery_partner__user_id=user_id)
        elif role in ['RESTAURANT', 'RESTAURANT_ADMIN']:
            return Orders.objects.filter(restaurant__user_id=user_id)
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

    @action(detail=True, methods=['post'])
    def auto_assign_partner(self, request, pk=None):
        user = request.user
        role = getattr(user, 'role', None)
        
        # Verify permissions: only Super Admins or Delivery Admins can trigger this
        if not getattr(user, 'is_superuser', False) and role not in ['SUPERADMIN', 'DELIVERY_ADMIN']:
            return Response({"error": "Permission denied. Only Delivery Admins can auto-assign orders."}, status=403)
            
        order = self.get_object()
        
        # Check order status
        if order.order_status not in ['PENDING', 'ACCEPTED', 'PREPARING', 'READY']:
            return Response({"error": f"Cannot assign partner to order with current status: {order.order_status}"}, status=400)
            
        # Check if already assigned
        existing_delivery = Delivery.objects.filter(order=order).first()
        if existing_delivery and existing_delivery.delivery_partner:
            return Response({"error": f"Order is already assigned to {existing_delivery.delivery_partner.name}"}, status=400)
            
        # Determine the target location for distance calculation (customer address)
        customer_location = None
        if order.address and order.address.location:
             customer_location = order.address.location
        elif order.restaurant and order.restaurant.location:
             # Fallback to restaurant location if no customer location is set
             customer_location = order.restaurant.location

        if not customer_location:
             return Response({"error": "Cannot determine destination location to find nearest partner"}, status=400)

        # 1. Filter: active, available partners who have a valid location
        partners = DeliveryPartner.objects.filter(is_active=True, is_available=True, current_location__isnull=False)
        
        # 2. Annotate: active orders count (Deliveries that are not delivered/cancelled)
        partners = partners.annotate(
            active_orders_count=Count('delivery', filter=~Q(delivery__delivery_status__in=['DELIVERED', 'CANCELLED']))
        )
        
        # 3. Annotate: distance to customer
        partners = partners.annotate(
            distance=Distance('current_location', customer_location)
        )

        # 4. Sort: First by fewest active orders, then by closest distance
        partners = partners.order_by('active_orders_count', 'distance')
        
        best_partner = partners.first()
        
        if not best_partner:
             return Response({"error": "No available delivery partners found online with valid locations."}, status=404)

        # Assign order to the absolute best partner
        with transaction.atomic():
            delivery, created = Delivery.objects.get_or_create(order=order, defaults={
                'delivery_status': 'ASSIGNED',
                'delivery_partner': best_partner
            })

            if not created:
                delivery.delivery_partner = best_partner
                delivery.delivery_status = 'ASSIGNED'
                delivery.save()

            order.order_status = 'ASSIGNED'
            order.delivery_partner = best_partner
            order.save()

            # Optional formatted distance message logic
            dist_str = "Unknown"
            if hasattr(best_partner.distance, 'm'):
                 dist_m = best_partner.distance.m
                 if dist_m < 1000:
                      dist_str = f"{round(dist_m)} meters"
                 else:
                      dist_str = f"{round(dist_m/1000, 2)} km"

        return Response({
            "message": "Order successfully assigned to the optimal delivery partner",
            "partner_id": best_partner.id,
            "partner_name": best_partner.name,
            "active_orders": getattr(best_partner, 'active_orders_count', 0),
            "distance": dist_str
        }, status=200)

    @action(detail=False, methods=['post'])
    def assign_partner(self, request):
        user = request.user
        role = getattr(user, 'role', None)
        
        # Verify permissions: only Super Admins or Delivery Admins can trigger this
        if not getattr(user, 'is_superuser', False) and role not in ['SUPERADMIN', 'DELIVERY_ADMIN']:
            return Response({"error": "Permission denied. Only Admins can manually assign orders."}, status=403)
            
        delivery_partner_id = request.data.get('delivery_partner_id')
        user_id = request.data.get('user_id')
        order_id = request.data.get('order_id')
        
        if not all([delivery_partner_id, user_id, order_id]):
            return Response({"error": "delivery_partner_id, user_id, and order_id are required fields."}, status=400)
            
        try:
            order = Orders.objects.get(id=order_id)
        except Orders.DoesNotExist:
            return Response({"error": "Order not found for the given order_id"}, status=404)
            
        try:
            partner = DeliveryPartner.objects.get(id=delivery_partner_id)
        except DeliveryPartner.DoesNotExist:
            return Response({"error": "Delivery partner not found"}, status=404)
            
        # Assign order explicitly to the given partner
        with transaction.atomic():
            delivery, created = Delivery.objects.get_or_create(order=order, defaults={
                'delivery_status': 'ASSIGNED',
                'delivery_partner': partner
            })

            if not created:
                if delivery.delivery_partner and delivery.delivery_partner != partner:
                    return Response({"error": f"Order is already assigned to another partner: {delivery.delivery_partner.name}"}, status=400)
                delivery.delivery_partner = partner
                delivery.delivery_status = 'ASSIGNED'
                delivery.save()

            order.order_status = 'ASSIGNED'
            order.delivery_partner = partner
            order.save()
            
        # Gather info for the response
        location = "Unknown"
        if order.address:
            location = f"{order.address.address_line_1}, {order.address.city.name}, {order.address.state.name}"
        elif order.restaurant:
            location = order.restaurant.location
            
        # Get food items
        food_items = OrderItem.objects.filter(order=order)
        food_item_details = [
            {"food_name": item.food_name, "quantity": item.quantity, "price": str(item.price)}
            for item in food_items
        ]
        
        order_details = {
            "order_id": order.id,
            "total_amount": str(order.total_amount),
            "order_status": order.order_status,
            "payment_status": order.payment_status,
            "restaurant_name": order.restaurant.name if order.restaurant else "Unknown"
        }

        return Response({
            "message": "Delivery partner successfully assigned to order",
            "assignment_details": {
                "delivery_partner_name": partner.name,
                "delivery_partner_phone": partner.phone
            },
            "location": location,
            "food_item_details": food_item_details,
            "order_details": order_details
        }, status=200)

    @action(detail=True, methods=['patch', 'post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        user = request.user
        role = getattr(user, 'role', None)

        if not new_status:
            return Response({"error": "status is required in request body"}, status=400)
            
        allowed_statuses = ['REACHED_RESTAURANT', 'PICKED_UP', 'OUT_FOR_DELIVERY', 'DELIVERED']
        if new_status not in allowed_statuses:
            return Response({"error": f"Delivery partners can only update status to: {', '.join(allowed_statuses)}"}, status=400)

        # Role checks
        is_superuser = getattr(user, 'is_superuser', False) or role == 'SUPERADMIN'
        delivery_roles = ['DELIVERY_PARTNER', 'DELIVERY_ADMIN']

        if not is_superuser and role not in delivery_roles:
            return Response({"error": "Only delivery staff can transition to this status"}, status=403)
        
        # Update timestamp and status logic
        if new_status == 'PICKED_UP':
            order.pickup_timestamp = timezone.now()
        elif new_status == 'DELIVERED':
            order.delivered_timestamp = timezone.now()

        order.order_status = new_status
        order.save()
        
        # Keep Delivery object status in sync
        delivery = Delivery.objects.filter(order=order).first()
        if delivery:
            delivery.delivery_status = new_status
            if new_status == 'DELIVERED':
                delivery.delivered_at = timezone.now()
            delivery.save()

        # Build response message exactly mapping to steps described
        status_messages = {
            'REACHED_RESTAURANT': 'Delivery partner has reached the restaurant.',
            'PICKED_UP': 'Food has been picked up by the delivery partner.',
            'OUT_FOR_DELIVERY': 'Delivery partner is out for delivery.',
            'DELIVERED': 'Order has been delivered successfully to the customer.'
        }
        message = status_messages.get(new_status, f"Order status successfully updated to {new_status}")

        return Response({
            "message": message,
            "order_id": order.id,
            "order_status": order.order_status,
            "user_id": order.user.id if order.user else None,
            "restaurant_id": order.restaurant.id if order.restaurant else None
        }, status=200)
