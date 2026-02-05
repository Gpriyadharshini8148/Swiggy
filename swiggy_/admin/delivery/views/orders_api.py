from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.delivery.models import Orders
from admin.delivery.serializers import OrdersSerializer
from admin.access.permissions import IsAuthenticatedUser
from admin.users.models import Users

class OrdersViewSet(viewsets.ModelViewSet):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer
    permission_classes = [IsAuthenticatedUser]

    def get_queryset(self):
        user_id = self.request.session.get('user_id')
        if not user_id:
            return Orders.objects.none()
        try:
            user = Users.objects.get(id=user_id)
            if user.role == 'ADMIN':
                return Orders.objects.all()
            else:
                return Orders.objects.filter(user_id=user_id)
        except Users.DoesNotExist:
            return Orders.objects.none()

    @action(detail=False, methods=['post'])
    def place_order(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user_id=request.session.get('user_id'))
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
        
    @action(detail=True, methods=['post'])
    def cancel_order(self, request, pk=None):
        order = self.get_object()
        if order.order_status in ['DELIVERED', 'CANCELLED']:
             return Response({"error": "Cannot cancel this order"}, status=400)
        
        order.order_status = 'CANCELLED'
        order.save()
        return Response({"message": "Order cancelled successfully"})
    
    @action(detail=True, methods=['get'])
    def track_order(self, request, pk=None):
        order = self.get_object()
        return Response({
            "order_id": order.id,
            "status": order.order_status,
            "delivery_partner": order.delivery_partner.name if hasattr(order, 'delivery_partner') and order.delivery_partner else None
        })
