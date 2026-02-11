from rest_framework import permissions
from admin.access.models import Users

class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        if getattr(request.user, 'is_superuser', False):
            return True
            
        return getattr(request.user, 'role', '') == 'SUPERADMIN'

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        if getattr(request.user, 'is_superuser', False):
            return True
            
        return getattr(request.user, 'role', '') in ['ADMIN', 'SUPERADMIN']

class IsAuthenticatedUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
