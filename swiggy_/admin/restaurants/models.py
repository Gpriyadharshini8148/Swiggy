from django.db import models
from admin.models import BaseModel, City

class Restaurant(BaseModel):
    name = models.CharField(max_length=255)
    logo_image_url = models.URLField(null=True, blank=True)
    banner_image_url = models.URLField(null=True, blank=True)
    location = models.CharField(max_length=255)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    category = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Customization(models.Model):
    suggestions = models.CharField(max_length=255)
    number_of_ingredients = models.IntegerField()

class FoodItem(BaseModel):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    food_image_url = models.URLField(null=True, blank=True)
    customization = models.JSONField(null=True, blank=True) # Changed to JSON as per schema 'customization json'
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_type = models.CharField(max_length=20, null=True, blank=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    is_veg = models.BooleanField(default=True)

    class Meta:
        unique_together = ('restaurant', 'name')

    def __str__(self):
        return self.name

class Cart(BaseModel):
    user = models.ForeignKey('users.Users', on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE) # As per schema
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE) # Redundant but requested
    quantity = models.IntegerField()

class Coupon(BaseModel):
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    coupon_image_url = models.URLField(null=True, blank=True)
    discount_type = models.CharField(max_length=20)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    scope = models.CharField(max_length=50)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True)
    expiry_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code