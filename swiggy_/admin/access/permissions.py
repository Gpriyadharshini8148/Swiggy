from rest_framework import permissions
from admin.users.models import Users

class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_superuser:
            return True  
        user_id = request.session.get('user_id')
        if not user_id:
            return False
        try:
            user = Users.objects.get(id=user_id)
            return user.role == 'ADMIN'
        except Users.DoesNotExist:
            return False
class IsAuthenticatedUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return True
        return bool(request.session.get('user_id'))
