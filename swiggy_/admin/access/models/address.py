from django.db import models
from .state_city import City, State
from .users import Users
from .base_model import BaseModel

class Address(BaseModel):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='addresses')
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    address_line_1 = models.TextField()
    address_line_2 = models.TextField(null=True, blank=True)
    landmark = models.CharField(max_length=255, null=True, blank=True)
    pincode = models.CharField(max_length=10)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    address_tag = models.CharField(max_length=50, default='Home') # Home, Work, etc.

    def __str__(self):
        return f"{self.user.username} - {self.address_tag}"

