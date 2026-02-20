from django.db import models
from .base_model import BaseModel

class Images(BaseModel):
    image = models.ImageField(upload_to='uploads/images/')
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.name or f"Image {self.id}"