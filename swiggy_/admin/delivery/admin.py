from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import DeliveryPartner, Orders, OrderItem

# Resources
class DeliveryPartnerResource(resources.ModelResource):
    class Meta:
        model = DeliveryPartner

class OrdersResource(resources.ModelResource):
    class Meta:
        model = Orders

class OrderItemResource(resources.ModelResource):
    class Meta:
        model = OrderItem

# Admin Classes
@admin.register(DeliveryPartner)
class DeliveryPartnerAdmin(ImportExportModelAdmin):
    resource_class = DeliveryPartnerResource
    list_display = ('name', 'phone', 'is_available', 'is_active', 'total_deliveries')
    search_fields = ('name', 'phone', 'email')
    list_filter = ('is_available', 'is_active', 'vehicle_type')

@admin.register(Orders)
class OrdersAdmin(ImportExportModelAdmin):
    resource_class = OrdersResource
    list_display = ('id', 'user', 'restaurant', 'total_amount', 'order_status', 'created_at')
    search_fields = ('id', 'user__username', 'restaurant__name')
    list_filter = ('order_status', 'created_at')

@admin.register(OrderItem)
class OrderItemAdmin(ImportExportModelAdmin):
    resource_class = OrderItemResource
    list_display = ('order', 'food_name', 'quantity', 'price')
    search_fields = ('order__id', 'food_name')
