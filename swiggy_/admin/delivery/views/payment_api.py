import razorpay
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ..models import Payment, Orders
from ..serializers import PaymentSerializer
from django.utils import timezone

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class RazorpayPaymentViewSet(viewsets.GenericViewSet):
    serializer_class = PaymentSerializer
    
    @action(detail=False, methods=['post'])
    def create_order(self, request):
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({"error": "Order ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order = Orders.objects.get(id=order_id)
            amount = int(order.total_amount * 100)
            
            data = {
                "amount": amount,
                "currency": "INR",
                "receipt": f"receipt_{order.id}",
                "payment_capture": 1 # Auto capture
            }
            
            razorpay_order = client.order.create(data=data)
            
            # Save or update payment record
            payment, created = Payment.objects.get_or_create(
                order=order,
                defaults={'payment_method': 'razorpay'}
            )
            payment.razorpay_order_id = razorpay_order['id']
            payment.save()
            
            return Response({
                "razorpay_order_id": razorpay_order['id'],
                "amount": amount,
                "currency": "INR",
                "key": settings.RAZORPAY_KEY_ID
            }, status=status.HTTP_200_OK)
            
        except Orders.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def verify_payment(self, request):
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')
        
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            # Verify the signature
            client.utility.verify_payment_signature(params_dict)
            
            # Update Payment status
            try:
                payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
                payment.razorpay_payment_id = razorpay_payment_id
                payment.transaction_id = razorpay_payment_id
                payment.razorpay_signature = razorpay_signature
                payment.payment_status = 'SUCCESS'
                payment.paid_at = timezone.now()
                payment.save()
                
                # Update Order Payment Status
                order = payment.order
                order.payment_status = 'PAID'
                order.save()
                
                return Response({"message": "Payment verified successfully"}, status=status.HTTP_200_OK)
            except Payment.DoesNotExist:
                return Response({"error": "Payment record not found"}, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({"error": "Signature verification failed", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)
