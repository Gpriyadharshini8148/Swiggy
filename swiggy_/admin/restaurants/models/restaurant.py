from django.db import models
from admin.models import BaseModel, City, State

class Restaurant(BaseModel):
    name = models.CharField(max_length=255)
    logo_image_url = models.URLField(null=True, blank=True)
    banner_image_url = models.URLField(null=True, blank=True)
    location = models.CharField(max_length=255)
    address = models.TextField(null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    category = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return self.name
