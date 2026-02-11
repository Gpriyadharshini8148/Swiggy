from django.db import models
from admin.access.models import BaseModel, Users
from .restaurant import Restaurant
from admin.delivery.models.orders import Orders

class Review(BaseModel):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reviews')
    order = models.OneToOneField(Orders, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1)
    comment = models.TextField(null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'order')

    def __str__(self):
        return f"{self.user.username} - {self.restaurant.name}"