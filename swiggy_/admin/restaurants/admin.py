from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from .models import Restaurant, Category, SubCategory, FoodItem, Cart, CartItem, Coupon

@admin.register(Restaurant)
class RestaurantAdmin(OSMGeoAdmin):
    list_display = ('name', 'city', 'rating', 'is_active')
    search_fields = ('name', 'location')
    list_filter = ('is_active', 'city')
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'category', 'sub_category', 'price', 'is_veg', 'is_both', 'is_available')
    list_filter = ('restaurant', 'category', 'sub_category', 'is_veg', 'is_both', 'is_available')
    search_fields = ('name',)

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'expiry_date', 'is_active')
    list_filter = ('is_active', 'discount_type')
    search_fields = ('code',)
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'restaurant')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'food_item', 'quantity')
