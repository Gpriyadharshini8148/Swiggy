from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Orders, Delivery, DeliveryPartner
from .serializers import OrdersSerializer, DeliverySerializer, DeliveryPartnerSerializer
from admin.access.permissions import IsSuperAdmin, IsAuthenticatedUser
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
        pass
    
    @action(detail=True, methods=['post'])
    def cancel_order(self, request, pk=None):
        pass
    
    @action(detail=True, methods=['get'])
    def track_order(self, request, pk=None):
        pass

class DeliveryPartnerViewSet(viewsets.ModelViewSet):
    queryset = DeliveryPartner.objects.all()
    serializer_class = DeliveryPartnerSerializer
    permission_classes = [IsAuthenticatedUser] 

    @action(detail=True, methods=['post'])
    def update_location(self, request, pk=None):
        pass

    @action(detail=True, methods=['post'])
    def accept_order(self, request, pk=None):
        pass
