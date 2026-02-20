from django.contrib.gis.db import models
from admin.access.models import BaseModel, Users, Images

class DeliveryPartner(BaseModel):
    user = models.OneToOneField(Users, on_delete=models.CASCADE, related_name='delivery_profile', null=True, blank=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(null=True, blank=True)
    profile_image = models.ForeignKey(Images, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle_type = models.CharField(max_length=50, null=True, blank=True)
    vehicle_number = models.CharField(max_length=50, null=True, blank=True)
    license_number = models.CharField(max_length=50, null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_deliveries = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True) # Online/Ready for orders
    current_location = models.PointField(srid=4326, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    def __str__(self):
        return self.name
