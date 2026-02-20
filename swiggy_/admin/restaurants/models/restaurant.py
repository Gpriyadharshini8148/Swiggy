from django.contrib.gis.db import models
from django.utils import timezone
from admin.access.models import BaseModel, City, State, Users, Images

class Restaurant(BaseModel):
    name = models.CharField(max_length=255)
    logo_image = models.ForeignKey(Images, related_name='restaurant_logo', on_delete=models.SET_NULL, null=True, blank=True)
    banner_image = models.ForeignKey(Images, related_name='restaurant_banner', on_delete=models.SET_NULL, null=True, blank=True)
    location = models.PointField(srid=4326, blank=True, null=True, help_text="Latitude and Longitude")
    address = models.TextField(null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    category = models.CharField(max_length=100, null=True, blank=True)
    user = models.OneToOneField(Users, on_delete=models.CASCADE, related_name='restaurant_profile', null=True, blank=True)
    
    # Operating Hours
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    
    # Bank & Tax Details
    account_number = models.CharField(max_length=20, null=True, blank=True)
    ifsc_code = models.CharField(max_length=15, null=True, blank=True)
    gst_number = models.CharField(max_length=20, null=True, blank=True)
    pan_number = models.CharField(max_length=15, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return self.name

    @property
    def is_open(self):
        if not self.is_active:
             return False
        
        now = timezone.localtime().time()
        if self.opening_time and self.closing_time:
            if self.opening_time < self.closing_time:
                return self.opening_time <= now <= self.closing_time
            else: # Overnight, e.g. 10 PM to 2 AM
                return now >= self.opening_time or now <= self.closing_time
        return True # Default to open if no times set