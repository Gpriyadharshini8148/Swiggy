from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from admin.delivery.models.orders import Orders
from admin.delivery.models.payment import Payment
from django.conf import settings
from django.utils import timezone
import razorpay

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def initiate_payment_api(request):
    order_id = request.data.get('order_id')
    if not order_id:
         return Response({"error": "order_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        if getattr(request.user, 'is_superuser', False) or getattr(request.user, 'role', None) == 'SUPERADMIN':
             order = Orders.objects.get(id=order_id)
        else:
             order = Orders.objects.get(id=order_id, user=request.user)
        
        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Create Razorpay order
        # amount is in paise
        razorpay_amount = int(order.total_amount * 100)
        razorpay_order = client.order.create({
            "amount": razorpay_amount,
            "currency": "INR",
            "receipt": f"receipt_{order.id}",
            "payment_capture": 1
        })
        
        # Create or Get Payment record
        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                'razorpay_order_id': razorpay_order['id'],
                'amount': order.total_amount,
                'payment_status': 'PENDING',
                'payment_method': 'RAZORPAY'
            }
        )
        if not created:
            payment.razorpay_order_id = razorpay_order['id']
            payment.amount = order.total_amount
            payment.payment_method = 'RAZORPAY'  # Ensure method is updated if retrying
            payment.save()
        
        return Response({
            "razorpay_order_id": razorpay_order['id'],
            "amount": order.total_amount,
            "currency": "INR",
            "razorpay_options": {
                "amount": razorpay_amount,
                "currency": "INR",
                "name": "Swiggy",
                "description": f"Order #{order.id}",
                "order_id": razorpay_order['id'],
                "prefill": {
                    "name": request.user.username if hasattr(request.user, 'username') else '',
                    "email": request.user.email if hasattr(request.user, 'email') else '',
                    "contact": request.user.phone if hasattr(request.user, 'phone') else ''
                },
                "theme": {
                    "color": "#F37254"
                }
            }
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
    
    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
         return Response({"error": "Missing required fields: razorpay_order_id, razorpay_payment_id, razorpay_signature"}, status=status.HTTP_400_BAD_REQUEST)
    
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
        # Update Payment and Order status
        payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
        payment.payment_status = 'COMPLETED'
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.transaction_id = razorpay_payment_id
        payment.paid_at = timezone.now()
        payment.save()
        
        order = payment.order
        order.payment_status = 'PAID'
        order.order_status = 'ACCEPTED'
        order.save()
        
        return Response({"message": "Payment confirmed successfully", "order_status": order.order_status})
        
    except Payment.DoesNotExist:
        return Response({"error": "Invalid razorpay_order_id. No payment record found for this ID."}, status=status.HTTP_404_NOT_FOUND)
    except razorpay.errors.SignatureVerificationError:
        return Response({"error": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)