from django.db import models
from admin.access.models import BaseModel

class Orders(BaseModel):
    user = models.ForeignKey('access.Users', on_delete=models.CASCADE)
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE)
    address = models.ForeignKey('access.Address', on_delete=models.SET_NULL, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    ORDER_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('PREPARING', 'Preparing'),
        ('READY', 'Ready for Pickup'),
        ('PICKED_UP', 'Picked Up'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    )
    
    order_status = models.CharField(max_length=50, choices=ORDER_STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=50, default='PENDING')
    
    # Customer Details
    customer_instructions = models.TextField(null=True, blank=True)
    preparation_timestamp = models.DateTimeField(null=True, blank=True)
    ready_timestamp = models.DateTimeField(null=True, blank=True)
    pickup_timestamp = models.DateTimeField(null=True, blank=True)
    delivered_timestamp = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Order {self.id}" 
