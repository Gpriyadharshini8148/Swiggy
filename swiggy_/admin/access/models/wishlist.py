from django.db import models
from .base_model import BaseModel
from .users import Users

class Wishlist(BaseModel):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    food_item = models.ForeignKey('restaurants.FoodItem', on_delete=models.CASCADE, null=True, blank=True)
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE, null=True, blank=True)
