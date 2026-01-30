from django.contrib import admin
from .models import Restaurant, Category, FoodItem, Cart, CartItem, Coupon

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'rating', 'is_active')
    search_fields = ('name', 'location')
    list_filter = ('is_active', 'city')
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'category', 'price', 'is_available')
    list_filter = ('restaurant', 'category', 'is_available', 'is_veg')
    search_fields = ('name',)

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'expiry_date', 'is_active')
    list_filter = ('is_active', 'discount_type')
    search_fields = ('code',)
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'restaurant')
