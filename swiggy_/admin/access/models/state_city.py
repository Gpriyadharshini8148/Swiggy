from django.db import models
from .base_model import BaseModel

class State(BaseModel):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.name

class City(BaseModel):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    city_code = models.CharField(max_length=20)
    is_serviceable = models.BooleanField(default=True)
    def __str__(self):
        return self.name