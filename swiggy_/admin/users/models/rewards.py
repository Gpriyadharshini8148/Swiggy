from django.db import models
from .users import Users

class Rewards(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    points_earned = models.IntegerField(default=0)
    points_redeemed = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
