from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.restaurants.models import FoodItem, Restaurant
from admin.restaurants.serializers import FoodItemSerializer
from admin.access.models import Users

class IsRestaurantOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of a restaurant or superadmins to edit food items.
    """
    def has_permission(self, request, view):
        # Allow read-only access to updated menu for authenticated users (or everyone if needed, but sticking to safer defaults)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions (POST, PUT, DELETE) for Superadmins
        if getattr(request.user, 'is_superuser', False) or getattr(request.user, 'role', None) == 'SUPERADMIN':
            return True

        # Write permissions for Restaurant Owners
        # Must be authenticated and have RESTAURANT role
        return request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'RESTAURANT'

class FoodItemViewSet(viewsets.ModelViewSet):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemSerializer
    permission_classes = [IsRestaurantOwnerOrAdmin]

    def get_queryset(self):
        # Optionally restricts the returned food items to a given restaurant,
        # by filtering against a "restaurant_id" query parameter in the URL.
        queryset = FoodItem.objects.all()
        restaurant_id = self.request.query_params.get('restaurant_id')
        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        
        # Auto-filter for restaurant owners if no specific ID requested
        user = self.request.user
        if not restaurant_id and user.is_authenticated and getattr(user, 'role', None) == 'RESTAURANT':
             try:
                 if isinstance(user, Users):
                     restaurant = Restaurant.objects.get(user=user)
                     queryset = queryset.filter(restaurant=restaurant)
             except Restaurant.DoesNotExist:
                 pass 

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        
        # If Superadmin, rely on serializer data (which should include restaurant ID)
        if getattr(user, 'is_superuser', False) or getattr(user, 'role', None) == 'SUPERADMIN':
            serializer.save()
            return

        # If Restaurant Owner, enforce their restaurant
        if getattr(user, 'role', None) == 'RESTAURANT' and isinstance(user, Users):
            try:
                restaurant = Restaurant.objects.get(user=user)
                serializer.save(restaurant=restaurant)
            except Restaurant.DoesNotExist:
                raise permissions.exceptions.PermissionDenied("You do not have a registered restaurant profile.")
        else:
             raise permissions.exceptions.PermissionDenied("You are not authorized to create food items.")

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=True, methods=['patch'])
    def toggle(self, request, pk=None):
        item = self.get_object()
        item.is_available = not item.is_available
        item.save()
        status_text = "Available" if item.is_available else "Unavailable"
        return Response({"message": f"Item is now {status_text}", "is_available": item.is_available})