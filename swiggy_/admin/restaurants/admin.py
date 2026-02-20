from django.contrib import admin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin
from .models import Restaurant, FoodItem, Coupon, Category, SubCategory
from admin.access.models import City, State, Users, Images

# Resources
class RestaurantResource(resources.ModelResource):
    city = fields.Field(
        column_name='city',
        attribute='city',
        widget=ForeignKeyWidget(City, 'name'))
    
    state = fields.Field(
        column_name='state',
        attribute='state',
        widget=ForeignKeyWidget(State, 'name'))
    
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(Users, 'id')) # Using ID as per spreadsheet
        
    logo_image = fields.Field(
        column_name='logo_image',
        attribute='logo_image',
        widget=ForeignKeyWidget(Images, 'name'))
        
    banner_image = fields.Field(
        column_name='banner_image',
        attribute='banner_image',
        widget=ForeignKeyWidget(Images, 'name'))

    class Meta:
        model = Restaurant
        exclude = ('location',) # Exclude location point field for now to avoid errors if format doesn't match

class RestaurantWidget(ForeignKeyWidget):
    def clean(self, value, row=None, **kwargs):
        if not value: return None
        value = str(value).strip()
        try:
            return self.model.objects.get(name__iexact=value)
        except self.model.DoesNotExist:
            raise ValueError(f"Restaurant '{value}' does not exist.")

class CategoryWidget(ForeignKeyWidget):
    def clean(self, value, row=None, **kwargs):
        if not value: return None
        value = str(value).strip()
        obj = self.model.objects.filter(name__iexact=value).first()
        if not obj:
            obj = self.model.objects.create(name=value)
        return obj

class SubCategoryWidget(ForeignKeyWidget):
    def clean(self, value, row=None, **kwargs):
        if not value: return None
        value = str(value).strip()
        category_name = row.get('category')
        category = None
        if category_name:
            category_name = str(category_name).strip()
            category = Category.objects.filter(name__iexact=category_name).first()
            if not category:
                category = Category.objects.create(name=category_name)
        obj = self.model.objects.filter(name__iexact=value, category=category).first()
        if not obj:
            obj = self.model.objects.create(name=value, category=category)
        return obj

class FoodItemResource(resources.ModelResource):
    restaurant = fields.Field(
        column_name='restaurant',
        attribute='restaurant',
        widget=RestaurantWidget(Restaurant, 'name'))
    
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=CategoryWidget(Category, 'name'))
    
    sub_category = fields.Field(
        column_name='sub_category',
        attribute='sub_category',
        widget=SubCategoryWidget(SubCategory, 'name'))
        
    food_image = fields.Field(
        column_name='food_image',
        attribute='food_image',
        widget=ForeignKeyWidget(Images, 'name'))

    class Meta:
        model = FoodItem
        import_id_fields = ('restaurant', 'name') # Use restaurant + name as unique identifier for updates
        skip_unchanged = True
        report_skipped = True
        exclude = ('id',) # Don't import ID, let DB generate it (unless updating by ID, but (restaurant, name) is better here)

class CouponResource(resources.ModelResource):
    class Meta:
        model = Coupon

class CategoryResource(resources.ModelResource):
    class Meta:
        model = Category

class SubCategoryResource(resources.ModelResource):
    class Meta:
        model = SubCategory

# Admin Classes
@admin.register(Restaurant)
class RestaurantAdmin(ImportExportModelAdmin):
    resource_class = RestaurantResource
    list_display = ('name', 'city', 'rating', 'is_active', 'is_open')
    search_fields = ('name', 'city__name')
    list_filter = ('city', 'is_active', 'is_verified')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if getattr(request.user, 'role', None) in ['RESTAURANT', 'RESTAURANT_ADMIN']:
            return qs.filter(user=request.user)
        return qs.none()

    def get_export_queryset(self, request):
        return self.get_queryset(request)
        
    def has_import_permission(self, request):
        return request.user.is_superuser or getattr(request.user, 'role', None) in ['RESTAURANT', 'RESTAURANT_ADMIN']

    def has_export_permission(self, request):
        return request.user.is_superuser or getattr(request.user, 'role', None) in ['RESTAURANT', 'RESTAURANT_ADMIN']

@admin.register(FoodItem)
class FoodItemAdmin(ImportExportModelAdmin):
    resource_class = FoodItemResource
    list_display = ('name', 'restaurant', 'category', 'price', 'is_available')
    search_fields = ('name', 'restaurant__name')
    list_filter = ('restaurant', 'category', 'is_available', 'is_veg')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if getattr(request.user, 'role', None) in ['RESTAURANT', 'RESTAURANT_ADMIN']:
            return qs.filter(restaurant__user=request.user)
        return qs.none()

    def get_export_queryset(self, request):
        return self.get_queryset(request)

    def has_import_permission(self, request):
        return request.user.is_superuser or getattr(request.user, 'role', None) in ['RESTAURANT', 'RESTAURANT_ADMIN']

    def has_export_permission(self, request):
        return request.user.is_superuser or getattr(request.user, 'role', None) in ['RESTAURANT', 'RESTAURANT_ADMIN']

@admin.register(Coupon)
class CouponAdmin(ImportExportModelAdmin):
    resource_class = CouponResource
    list_display = ('code', 'discount_type', 'discount_value', 'expiry_date', 'is_active')
    search_fields = ('code',)
    list_filter = ('discount_type', 'is_active')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if getattr(request.user, 'role', None) in ['RESTAURANT', 'RESTAURANT_ADMIN']:
             # Assuming Coupon has 'restaurant' field. Let's verify model or just filter safely
             if hasattr(Coupon, 'restaurant'):
                 return qs.filter(restaurant__user=request.user)
             return qs # If global coupon, maybe restrict? Or allow. Let's assume restaurant linked.
        return qs.none()

    def get_export_queryset(self, request):
        return self.get_queryset(request)

    def has_import_permission(self, request):
        return request.user.is_superuser or getattr(request.user, 'role', None) in ['RESTAURANT', 'RESTAURANT_ADMIN']

    def has_export_permission(self, request):
        return request.user.is_superuser or getattr(request.user, 'role', None) in ['RESTAURANT', 'RESTAURANT_ADMIN']

@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    resource_class = CategoryResource
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(SubCategory)
class SubCategoryAdmin(ImportExportModelAdmin):
    resource_class = SubCategoryResource
    list_display = ('name', 'category')
    search_fields = ('name', 'category__name')
    list_filter = ('category',)
