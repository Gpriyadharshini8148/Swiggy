from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.delivery.models import DeliveryPartner, Orders, Delivery
from admin.delivery.serializers import DeliveryPartnerSerializer, DeliverySerializer
from admin.access.permissions import IsAuthenticatedUser
from django.utils import timezone
class DeliveryPartnerViewSet(viewsets.ModelViewSet):
    queryset = DeliveryPartner.objects.all()
    serializer_class = DeliveryPartnerSerializer
    permission_classes = [IsAuthenticatedUser] 

    @action(detail=True,methods=['patch'])
    def status_detail(self,request):
        partner=self.get_object()
        if not partner.is_verified:
            return Response({'message':'delivery partner not verified'},status=403)
        is_online=False
        if is_online is True:
            partner.is_active=True
            partner.save()
            return Response({'message':'delivery partner is now online'},status=200)
        elif is_online is False:
            partner.is_active=False
            return Response({'message':'delivery partner is now in offline'},status=401)
        else:
            return Response({'message':'invalid status provided right now the delivery partner is un available'})
    @action(detail=True,methods=['post'])
    def update_location_detail(self,request):
        partner=self.get_object()
        latitude=request.data.get('latitude')
        lagitude=request.data.get('lagitude')
        if latitude is None:
            return Response({'error':'latitude is required'},status=400)
        if lagitude is None:
            return Response({'error':'lagitude is requierd'},status=400)
        return Response({"message":"location updated successfully"},status=203)
    @action(detail=True, methods=['post'])
    def accept_order_detail(self, request, pk=None):
        partner = self.get_object()
        order_id = request.data.get('order_id')         
        if not order_id:
            return Response({"error": "Order ID is required"}, status=400)
        
        try:
            order = Orders.objects.get(id=order_id)
            if order.order_status not in ['PENDING', 'READY_FOR_ASSIGNMENT']: 
                return Response({"error": "Order cannot be accepted (Status: {})".format(order.order_status)}, status=400)
            delivery, created = Delivery.objects.get_or_create(order=order, defaults={
                'delivery_status': 'ASSIGNED',
                'delivery_partner': partner
            })
            
            if not created:
                if delivery.delivery_partner and delivery.delivery_partner != partner:
                    return Response({"error": "Order already assigned to another partner"}, status=400)
                delivery.delivery_partner = partner
                delivery.delivery_status = 'ASSIGNED'
                delivery.save()
            order.order_status = 'ASSIGNED'
            order.save()
            
            return Response({"message": "Order assigned successfully", "order_id": order.id, "delivery_id": delivery.id})
        except Orders.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)
    @action(detail=True, methods=['post'])
    def reject_order_detail(self, request, pk=None):
        partner = self.get_object()
        order_id = request.data.get('order_id')
        return Response({"message": "Order rejected. Looking for next partner."})
    @action(detail=True, methods=['post'])
    def update_delivery_status_detail(self, request, pk=None):
        partner = self.get_object()
        delivery_id = request.data.get('delivery_id')
        new_status = request.data.get('status')
        valid_statuses = ['REACHED_RESTAURANT', 'PICKED_UP', 'OUT_FOR_DELIVERY', 'DELIVERED']
        if new_status not in valid_statuses:
             return Response({"error":"Invalid status. Allowed: {}".format(valid_statuses)}, status=400)   
        try:
            delivery = Delivery.objects.get(id=delivery_id, delivery_partner=partner)
            delivery.delivery_status = new_status
            
            if new_status == 'DELIVERED':
                delivery.delivered_at = timezone.now()
                order_total = delivery.order.total_amount
                earnings = 20 + (float(order_total) * 0.05) 
                partner.total_deliveries += 1
                partner.save()
                delivery.order.order_status = 'DELIVERED'
                delivery.order.payment_status = 'PAID' 
                delivery.order.save()
                
                delivery.save()
                return Response({"message": "Order Delivered!", "earnings": earnings})
            delivery.order.order_status = new_status
            delivery.order.save()
            delivery.save()
            
            return Response({"message": "Status updated to {}".format(new_status)})
            
        except Delivery.DoesNotExist:
             return Response({"error": "Delivery task not found for this partner"}, status=404)

