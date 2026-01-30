from django.contrib import admin
from .models import State, City

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'city_code', 'is_serviceable')
