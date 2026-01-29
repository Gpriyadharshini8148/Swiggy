from django.contrib import admin
from .models import UserAuth

@admin.register(UserAuth)
class UserAuthAdmin(admin.ModelAdmin):
    list_display = ('user', 'auth_type', 'is_verified', 'last_login')
    list_filter = ('auth_type', 'is_verified')
