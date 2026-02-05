from django.db import models
from admin.models import BaseModel, City, State
from .users import Users

class Address(BaseModel):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    address_line = models.TextField()
    landmark = models.CharField(max_length=255, null=True, blank=True)
    pincode = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)
    address_tag = models.CharField(max_length=50)
