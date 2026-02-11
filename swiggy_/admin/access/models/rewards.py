from django.db import models
from .base_model import BaseModel
from .users import Users

class Rewards(BaseModel):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    points_earned = models.IntegerField(default=0)
    points_redeemed = models.IntegerField(default=0)
