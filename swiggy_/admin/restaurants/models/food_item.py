from django.db import models
from admin.access.models import BaseModel, Images
from .restaurant import Restaurant
from .category import Category, SubCategory

class FoodItem(BaseModel):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    sub_category = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    food_image = models.ForeignKey(Images, on_delete=models.SET_NULL, null=True, blank=True)
    customization = models.JSONField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    DISCOUNT_CHOICES = (
        ('Percentage', 'Percentage'),('Flat', 'Flat'),)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_CHOICES, null=True, blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    is_veg = models.BooleanField(default=True)
    is_both = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    
    class Meta:
        unique_together = ('restaurant', 'name')
    def __str__(self):
        return self.name
