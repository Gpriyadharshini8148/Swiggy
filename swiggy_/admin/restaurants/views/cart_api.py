from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.restaurants.models import Cart, CartItem, FoodItem
from admin.restaurants.serializers import CartSerializer, CartItemSerializer
from admin.access.models import Users

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer

    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated:
            # Allow super admin to see all carts
            if getattr(user, 'role', None) == 'SUPERADMIN':
                return Cart.objects.all()
            if isinstance(user, Users):
                return Cart.objects.filter(user=user)
        
        user_id = self.request.session.get('user_id')
        if user_id:
            return Cart.objects.filter(user_id=user_id)
            
        return Cart.objects.none()

    def _get_cart_user(self, request):
        if isinstance(request.user, Users):
            return request.user
        
        if getattr(request.user, 'role', None) == 'SUPERADMIN' or getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False):
            # Check data and query_params for user identifier
            user_id = (request.data.get('user_id') or 
                       request.query_params.get('user_id') or 
                       request.data.get('user') or 
                       request.query_params.get('user') or
                       request.session.get('user_id'))
            
            if user_id:
                try:
                    # In case user_id is passed as a string or int
                    return Users.objects.get(id=user_id)
                except (Users.DoesNotExist, ValueError):
                    return None
        return None

    @action(detail=False, methods=['get'])
    def my_cart(self, request):
        target_user = self._get_cart_user(request)
        if not target_user:
             return Response({"error": "Valid User/User ID required for cart access. Admins must provide 'user' or 'user_id'."}, status=status.HTTP_400_BAD_REQUEST)

        cart, created = Cart.objects.get_or_create(user=target_user)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        target_user = self._get_cart_user(request)
        if not target_user:
            return Response({"error": "Valid User/User ID required for cart access. Admins must provide 'user' or 'user_id'."}, status=status.HTTP_400_BAD_REQUEST)
            
        food_item_id = request.data.get('item_id')
        if not food_item_id:
            return Response({"error": "item_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        quantity = int(request.data.get('qty', 1))
        
        try:
            food_item = FoodItem.objects.get(id=food_item_id)
            restaurant = food_item.restaurant
            
            cart, created = Cart.objects.get_or_create(user=target_user)
            
            # Check if cart already has items from a different restaurant
            if cart.restaurant and cart.restaurant != restaurant:
                # If there are items in the cart from another restaurant, return conflict
                if CartItem.objects.filter(cart=cart).exists():
                    return Response({
                        "error": "Different restaurant detected",
                        "message": f"Your cart contains items from {cart.restaurant.name}. Do you want to clear it and add this item?"
                    }, status=status.HTTP_409_CONFLICT)
            
            cart.restaurant = restaurant
            cart.save()
            
            # Add or update item
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart, 
                food_item=food_item,
                defaults={'quantity': quantity}
            )
            if not created:
                cart_item.quantity += quantity
            cart_item.save()
            
            return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)
            
        except FoodItem.DoesNotExist:
            return Response({"error": "Food item not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """
        Toggles an item in the cart:
        - If item exists, remove it.
        - If item does not exist, add it (qty 1).
        """
        target_user = self._get_cart_user(request)
        if not target_user:
            return Response({"error": "Valid User/User ID required for cart access. Admins must provide 'user' or 'user_id'."}, status=status.HTTP_400_BAD_REQUEST)
            
        food_item_id = request.data.get('item_id')
        if not food_item_id:
            return Response({"error": "item_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            food_item = FoodItem.objects.get(id=food_item_id)
            
            cart, created = Cart.objects.get_or_create(user=target_user)
            
            # Check if item exists in cart
            cart_item = CartItem.objects.filter(cart=cart, food_item=food_item).first()
            
            if cart_item:
                # CASE: Remove item
                cart_item.delete()
                
                # If cart is now empty, clear the restaurant association
                if not CartItem.objects.filter(cart=cart).exists():
                    cart.restaurant = None
                    cart.save()
                    
                return Response({
                    "message": "Removed from cart", 
                    "added": False,
                    "cart_data": CartSerializer(cart).data
                }, status=status.HTTP_200_OK)
            else:
                # CASE: Add item
                restaurant = food_item.restaurant
                
                # Check restaurant conflict
                if cart.restaurant and cart.restaurant != restaurant:
                    if CartItem.objects.filter(cart=cart).exists():
                        return Response({
                            "error": "Different restaurant detected",
                            "message": f"Your cart contains items from {cart.restaurant.name}. Do you want to clear it and add this item?"
                        }, status=status.HTTP_409_CONFLICT)
                
                cart.restaurant = restaurant
                cart.save()
                
                CartItem.objects.create(cart=cart, food_item=food_item, quantity=1)
                
                return Response({
                    "message": "Added to cart", 
                    "added": True, 
                    "cart_data": CartSerializer(cart).data
                }, status=status.HTTP_200_OK)
                
        except FoodItem.DoesNotExist:
            return Response({"error": "Food item not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def price_summary(self, request):
        target_user = self._get_cart_user(request)
        if not target_user:
            return Response({"error": "Valid User/User ID required for cart access. Admins must provide 'user' or 'user_id'."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cart = Cart.objects.get(user=target_user)
            items = CartItem.objects.filter(cart=cart)
            
            if not items.exists():
                return Response({"error": "Cart is empty"}, status=status.HTTP_404_NOT_FOUND)
                
            item_total = sum(item.food_item.price * item.quantity for item in items)
            gst = float(item_total) * 0.05 # 5% GST
            packing_charges = 20.00
            delivery_fee = 30.00
            discount = 0.00 # Logic for coupons would go here
            
            grand_total = float(item_total) + float(gst) + packing_charges + delivery_fee - discount
            
            return Response({
                "item_total": item_total,
                "gst": gst,
                "packing_charges": packing_charges,
                "delivery_fee": delivery_fee,
                "discount": discount,
                "grand_total": grand_total
            })
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def clear_cart(self, request):
        target_user = self._get_cart_user(request)
        if not target_user:
            return Response({"error": "Valid User/User ID required for cart access. Admins must provide 'user' or 'user_id'."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cart = Cart.objects.get(user=target_user)
            CartItem.objects.filter(cart=cart).delete()
            cart.restaurant = None
            cart.save()
            return Response({"message": "Cart cleared successfully"})
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        target_user = self._get_cart_user(request)
        if not target_user:
             return Response({"error": "Valid User/User ID required for cart access. Admins must provide 'user' or 'user_id'."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cart = Cart.objects.get(user=target_user)
            cart_items = CartItem.objects.filter(cart=cart)
            
            if not cart_items.exists():
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
                
            total_amount = sum(item.food_item.price * item.quantity for item in cart_items)
            
            return Response({
                "message": "Checkout initiated",
                "total_amount": total_amount,
                "item_count": cart_items.count()
            })
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)
