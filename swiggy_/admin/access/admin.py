from django.contrib import admin
from .models import Users, State, City, Address, Rewards, Wishlist

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'city_code', 'is_serviceable')

@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone', 'role', 'is_verified')
    list_filter = ('role', 'is_verified')

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address_tag', 'city', 'state', 'pincode', 'is_default')
    list_filter = ('address_tag', 'is_default')
    search_fields = ('user__username', 'pincode', 'city__name')

@admin.register(Rewards)
class RewardsAdmin(admin.ModelAdmin):
    list_display = ('user', 'points_earned', 'points_redeemed')
    search_fields = ('user__username',)

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'food_item')
    search_fields = ('user__username', 'food_item__name')