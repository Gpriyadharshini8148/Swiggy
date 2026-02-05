from django.db import models
from admin.models import BaseModel
from .orders import Orders

class OrderCoupon(BaseModel):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    coupon = models.ForeignKey('restaurants.Coupon', on_delete=models.CASCADE)
