from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.restaurants.models import Cart, CartItem, FoodItem
from admin.restaurants.serializers import CartSerializer, CartItemSerializer
from admin.access.models import Users

class UserCartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def _get_cart(self, request):
        user = request.user
        if isinstance(user, Users):
             cart, created = Cart.objects.get_or_create(user=user)
             return cart
        
        # If user is simple_jwt User or similar but not our Users model instance
        # Try fetching the actual Users instance
        if user.is_authenticated:
            try:
                # Assuming username or id maps correctly
                actual_user = Users.objects.get(id=user.id)
                cart, created = Cart.objects.get_or_create(user=actual_user)
                return cart
            except Users.DoesNotExist:
                pass
        
        return None

    @action(detail=False, methods=['get'])
    def my_cart(self, request):
        cart = self._get_cart(request)
        items = CartItem.objects.filter(cart=cart)
        serializer = CartItemSerializer(items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """
        Use this for incrementing quantity or specific adds.
        """
        food_item_id = request.data.get('item_id') or request.query_params.get('item_id')
        if not food_item_id:
            return Response({"error": "item_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        qty_param = request.data.get('qty') or request.query_params.get('qty')
        try:
            quantity = int(qty_param) if qty_param is not None else 1
            if quantity not in [1, -1]:
                return Response({"error": "Quantity must be 1 or -1"}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({"error": "Invalid quantity parameter"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            food_item = FoodItem.objects.get(id=food_item_id)
            restaurant = food_item.restaurant
            cart = self._get_cart(request)
            
            # Check if cart already has items from a different restaurant
            if cart.restaurant and cart.restaurant != restaurant:
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
                
            if cart_item.quantity <= 0:
                cart_item.delete()
                
                # If cart is now empty, clear the restaurant association
                if not CartItem.objects.filter(cart=cart).exists():
                    cart.restaurant = None
                    cart.save()
                    return Response({"message": "Cart is empty"}, status=status.HTTP_200_OK)
                
                return Response({"message": "Item removed from cart"}, status=status.HTTP_200_OK)
            else:
                cart_item.save()
            
            message = "Added to cart" if quantity > 0 else "1 item removed from cart"
            return Response({"message": message}, status=status.HTTP_200_OK)
            
        except FoodItem.DoesNotExist:
            return Response({"error": "Food item not found"}, status=status.HTTP_404_NOT_FOUND)
    @action(detail=False, methods=['get'])
    def price_summary(self, request):
        try:
            cart = Cart.objects.get(user=request.user)
            items = CartItem.objects.filter(cart=cart)
            
            if not items.exists():
                return Response({'error': 'Cart is empty'}, status=status.HTTP_200_OK) # Or 404, but 200 with empty fields might be safer for UI
                
            item_total = sum(item.food_item.price * item.quantity for item in items)
            gst = float(item_total) * 0.05 
            packing_charges = 20.00
            delivery_fee = 30.00
            discount = 0.00 
            
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
