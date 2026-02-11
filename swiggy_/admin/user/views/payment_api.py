from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from admin.delivery.models.orders import Orders
from admin.delivery.models.payment import Payment
from django.conf import settings
import razorpay

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def initiate_payment_api(request):
    order_id = request.data.get('order_id')
    try:
        order = Orders.objects.get(id=order_id, user=request.user)
        
        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Create Razorpay order
        # amount is in paise
        razorpay_order = client.order.create({
            "amount": int(order.total_amount * 100),
            "currency": "INR",
            "receipt": f"receipt_{order.id}"
        })
        
        # Create Payment record
        Payment.objects.create(
            order=order,
            payment_id=razorpay_order['id'],
            amount=order.total_amount,
            status='PENDING',
            payment_method='RAZORPAY'
        )
        
        return Response({
            "razorpay_order_id": razorpay_order['id'],
            "amount": order.total_amount,
            "currency": "INR",
            "key": settings.RAZORPAY_KEY_ID
        })
    except Orders.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def confirm_payment_api(request):
    razorpay_order_id = request.data.get('razorpay_order_id')
    razorpay_payment_id = request.data.get('razorpay_payment_id')
    razorpay_signature = request.data.get('razorpay_signature')
    
    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Verify signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        client.utility.verify_payment_signature(params_dict)
        
        # Update Payment and Order status
        payment = Payment.objects.get(payment_id=razorpay_order_id)
        payment.status = 'COMPLETED'
        payment.transaction_id = razorpay_payment_id
        payment.save()
        
        order = payment.order
        order.payment_status = 'PAID'
        order.status = 'CONFIRMED'
        order.save()
        
        return Response({"message": "Payment confirmed successfully", "order_status": order.status})
        
    except razorpay.errors.SignatureVerificationError:
        return Response({"error": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
