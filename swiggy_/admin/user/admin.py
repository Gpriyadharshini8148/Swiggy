from django.contrib import admin
from .models import ServiceableZone, Notification

@admin.register(ServiceableZone)
class ServiceableZoneAdmin(admin.ModelAdmin):
    list_display = ('zone_name', 'city', 'radius_km', 'is_active')
    list_filter = ('is_active', 'city')
    search_fields = ('zone_name', 'city__name')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    ordering = ('-created_at',)