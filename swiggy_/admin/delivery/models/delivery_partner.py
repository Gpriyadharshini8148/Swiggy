from django.db import models
from admin.models import BaseModel

class DeliveryPartner(BaseModel):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(null=True, blank=True)
    profile_image_url = models.URLField(null=True, blank=True)
    vehicle_type = models.CharField(max_length=50, null=True, blank=True)
    vehicle_number = models.CharField(max_length=50, null=True, blank=True)
    license_number = models.CharField(max_length=50, null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_deliveries = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.name
