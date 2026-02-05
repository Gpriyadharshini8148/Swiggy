from django.db import models
from admin.models import BaseModel
from .orders import Orders
from .delivery_partner import DeliveryPartner

class Delivery(BaseModel):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    delivery_partner = models.ForeignKey(DeliveryPartner, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_status = models.CharField(max_length=50)
    delivered_at = models.DateTimeField(null=True, blank=True)
