from django.db import models
from admin.models import BaseModel

class Orders(BaseModel):
    user = models.ForeignKey('users.Users', on_delete=models.CASCADE)
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE)
    address = models.ForeignKey('users.Address', on_delete=models.SET_NULL, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_status = models.CharField(max_length=50, default='PENDING')
    payment_status = models.CharField(max_length=50, default='PENDING')
    
    def __str__(self):
        return f"Order {self.id}"
