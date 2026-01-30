"""
URL configuration for swiggy_ project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('admin.urls')), # Include our custom admin app urls at root
]
