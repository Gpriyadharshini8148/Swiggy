from django.db import models
from admin.access.models import BaseModel
from .orders import Orders

class OrderItem(BaseModel):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    food_item = models.ForeignKey('restaurants.FoodItem', on_delete=models.SET_NULL, null=True, blank=True)
    food_name = models.CharField(max_length=255)
    food_image = models.ImageField(upload_to='orders/items/', null=True, blank=True)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.food_name} x {self.quantity}"
