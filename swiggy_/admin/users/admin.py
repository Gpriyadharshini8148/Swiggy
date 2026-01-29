from django.contrib import admin
from .models import Users, Address, Wishlist, Rewards

@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    search_fields = ('name', 'email', 'phone')

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'pincode', 'is_default')

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'food_item')

@admin.register(Rewards)
class RewardsAdmin(admin.ModelAdmin):
    list_display = ('user', 'points_earned', 'points_redeemed')
