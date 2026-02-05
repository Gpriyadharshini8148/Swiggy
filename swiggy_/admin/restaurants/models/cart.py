from django.db import models
from admin.models import BaseModel
from .food_item import FoodItem
from .restaurant import Restaurant

class Cart(BaseModel):
    user = models.ForeignKey('users.Users', on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
