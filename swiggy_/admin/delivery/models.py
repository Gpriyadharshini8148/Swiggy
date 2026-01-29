from django.db import models
from admin.models import BaseModel
from admin.users.models import Users, Address
from admin.restaurants.models import Restaurant, FoodItem, Coupon

class Orders(BaseModel):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    order_status = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=50)

    def __str__(self):
        return f"Order {self.id}"

class OrderItem(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    food_name = models.CharField(max_length=255)
    food_image_url = models.URLField(null=True, blank=True)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

class OrderCoupon(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)

class Payment(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100)
    paid_at = models.DateTimeField(null=True, blank=True)

class Delivery(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    delivery_status = models.CharField(max_length=50)
    delivered_at = models.DateTimeField(null=True, blank=True)
class DeliveryPartner(BaseModel):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField()
    profile_image_url = models.URLField(null=True, blank=True)
    
    vehicle_type = models.CharField(max_length=50)
    vehicle_number = models.CharField(max_length=50)
    license_number = models.CharField(max_length=50)
    
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_deliveries = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

