from django.db import models
from admin.access.models import BaseModel
from .food_item import FoodItem
from .restaurant import Restaurant

class Cart(BaseModel):
    user = models.ForeignKey('access.Users', on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Cart for {self.user.username}"
