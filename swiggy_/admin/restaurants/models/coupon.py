from django.db import models
from admin.models import BaseModel
from .restaurant import Restaurant

class Coupon(BaseModel):
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    coupon_image_url = models.URLField(null=True, blank=True)
    DISCOUNT_CHOICES = (
        ('Percentage', 'Percentage'),
        ('Flat', 'Flat'),
    )
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    scope = models.CharField(max_length=50)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True)
    expiry_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code
