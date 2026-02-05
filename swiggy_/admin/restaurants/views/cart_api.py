from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.restaurants.models import Cart
from admin.restaurants.serializers import CartSerializer

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    @action(detail=False, methods=['get'])
    def my_cart(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
            return Response({"error": "User not authenticated"}, status=401)
        cart_items = Cart.objects.filter(user_id=user_id)
        serializer = self.get_serializer(cart_items, many=True)
        return Response(serializer.data)
    @action(detail=False, methods=['post'])
    def clear_cart(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
             return Response({"error": "User not authenticated"}, status=401)
        Cart.objects.filter(user_id=user_id).delete()
        return Response({"message": "Cart cleared successfully"})
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
             return Response({"error": "User not authenticated"}, status=401)
        cart_items = Cart.objects.filter(user_id=user_id)
        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=400)
        total_amount = sum(item.food_item.price for item in cart_items)
        return Response({
            "message": "Checkout initiated",
            "total_amount": total_amount,
            "item_count": cart_items.count()
        })
