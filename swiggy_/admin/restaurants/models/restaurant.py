from django.db import models
from admin.access.models import BaseModel, City, State, Users

class Restaurant(BaseModel):
    name = models.CharField(max_length=255)
    logo_image_url = models.URLField(null=True, blank=True,max_length=500)
    banner_image_url = models.URLField(null=True, blank=True,max_length=500)
    location = models.CharField(max_length=255)
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