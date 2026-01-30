from django.db import models
from admin.models import BaseModel, City, State

class Users(BaseModel):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('USER', 'User'),
        ('RESTAURANT', 'Restaurant'),
        ('DELIVERY', 'Delivery'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='USER')
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    password_hash = models.TextField(null=True, blank=True)
    profile_image_url = models.URLField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    deleted_by = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

class Address(BaseModel):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    address_line = models.TextField()
    landmark = models.CharField(max_length=255, null=True, blank=True)
    pincode = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)
    address_tag = models.CharField(max_length=50)

class Wishlist(BaseModel):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    food_item = models.ForeignKey('restaurants.FoodItem', on_delete=models.CASCADE)
    deleted_at = models.DateTimeField(null=True, blank=True)

class Rewards(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    points_earned = models.IntegerField(default=0)
    points_redeemed = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)