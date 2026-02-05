from django.db import models
from admin.models import BaseModel
from .users import Users

class Wishlist(BaseModel):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    food_item = models.ForeignKey('restaurants.FoodItem', on_delete=models.CASCADE)
    deleted_at = models.DateTimeField(null=True, blank=True)
