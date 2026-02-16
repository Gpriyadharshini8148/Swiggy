from django.db import models
from admin.access.models import BaseModel
from .orders import Orders

class Payment(BaseModel):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50) 
    payment_status = models.CharField(max_length=50, default='PENDING')
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
