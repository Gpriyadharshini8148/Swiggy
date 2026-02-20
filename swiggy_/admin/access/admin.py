from django.contrib import admin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin
from .models import Users, Address, Rewards, Wishlist, State, City, Images

# Resources for Import/Export
class UsersResource(resources.ModelResource):
    class Meta:
        model = Users
        fields = ('id', 'username', 'email', 'phone', 'role', 'is_verified', 'is_active')

class AddressResource(resources.ModelResource):
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(Users, 'username'))

    class Meta:
        model = Address

class RewardsResource(resources.ModelResource):
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(Users, 'username'))

    class Meta:
        model = Rewards

class WishlistResource(resources.ModelResource):
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(Users, 'username'))

    class Meta:
        model = Wishlist

class StateResource(resources.ModelResource):
    class Meta:
        model = State

class CityResource(resources.ModelResource):
    class Meta:
        model = City

class ImagesResource(resources.ModelResource):
    class Meta:
        model = Images

# Admin Classes
@admin.register(Users)
class UsersAdmin(ImportExportModelAdmin):
    resource_class = UsersResource
    list_display = ('id', 'username', 'email', 'phone', 'role', 'is_active', 'is_verified')
    search_fields = ('username', 'email', 'phone')
    list_filter = ('role', 'is_active', 'is_verified')
    
    def has_import_permission(self, request):
        return request.user.is_superuser
        
    def has_export_permission(self, request):
        return request.user.is_superuser

@admin.register(Address)
class AddressAdmin(ImportExportModelAdmin):
    resource_class = AddressResource
    list_display = ('user', 'address_line_1', 'city', 'state', 'pincode', 'is_default')
    search_fields = ('user__username', 'address_line_1', 'pincode')
    list_filter = ('city', 'state', 'is_default')

@admin.register(Rewards)
class RewardsAdmin(ImportExportModelAdmin):
    resource_class = RewardsResource
    list_display = ('user', 'points_earned', 'points_redeemed', 'is_active')
    search_fields = ('user__username',)

@admin.register(Wishlist)
class WishlistAdmin(ImportExportModelAdmin):
    resource_class = WishlistResource
    list_display = ('user', 'restaurant', 'food_item', 'created_at')
    search_fields = ('user__username', 'restaurant__name', 'food_item__name')

@admin.register(State)
class StateAdmin(ImportExportModelAdmin):
    resource_class = StateResource
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(City)
class CityAdmin(ImportExportModelAdmin):
    resource_class = CityResource
    list_display = ('name', 'state')
    search_fields = ('name', 'state__name')
    list_filter = ('state',)

@admin.register(Images)
class ImagesAdmin(ImportExportModelAdmin):
    resource_class = ImagesResource
    list_display = ('name', 'image', 'created_at')
    search_fields = ('name',)