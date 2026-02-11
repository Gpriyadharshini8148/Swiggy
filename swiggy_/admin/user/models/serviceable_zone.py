from django.db import models
from admin.access.models.base_model import BaseModel
from admin.access.models.state_city import City

class ServiceableZone(BaseModel):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='serviceable_zones')
    zone_name = models.CharField(max_length=100)
    # Using center and radius for simple serviceability check without PostGIS
    center_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    center_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    radius_km = models.DecimalField(max_digits=5, decimal_places=2, help_text="Delivery radius in kilometers")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.zone_name} ({self.city.name})"
