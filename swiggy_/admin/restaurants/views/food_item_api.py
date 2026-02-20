from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.restaurants.models import FoodItem, Restaurant
from admin.restaurants.serializers import FoodItemSerializer
from admin.access.models import Users
from rest_framework.parsers import MultiPartParser
from django.http import HttpResponse
from tablib import Dataset
from admin.restaurants.admin import FoodItemResource

class IsRestaurantOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of a restaurant or superadmins to edit food items.
    """
    def has_permission(self, request, view):
        # Specific permissions for import/export
        if getattr(view, 'action', None) in ['export_csv', 'import_csv']:
            return getattr(request.user, 'is_superuser', False) or getattr(request.user, 'role', None) in ['SUPERADMIN', 'RESTAURANT', 'RESTAURANT_ADMIN']

        # Allow read-only access to updated menu for authenticated users (or everyone if needed, but sticking to safer defaults)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions (POST, PUT, DELETE) for Superadmins
        if getattr(request.user, 'is_superuser', False) or getattr(request.user, 'role', None) == 'SUPERADMIN':
            return True

        # Write permissions for Restaurant Owners and Admins
        return request.user and request.user.is_authenticated and getattr(request.user, 'role', None) in ['RESTAURANT', 'RESTAURANT_ADMIN']

class FoodItemViewSet(viewsets.ModelViewSet):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemSerializer
    permission_classes = [IsRestaurantOwnerOrAdmin]

    def get_queryset(self):
        queryset = FoodItem.objects.all()
        restaurant_id = self.request.query_params.get('restaurant_id')
        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        
        user = self.request.user
        
        if getattr(self, 'action', None) == 'export_csv':
            # In export, strictly restrict based on role
            if getattr(user, 'is_superuser', False) or getattr(user, 'role', None) == 'SUPERADMIN':
                pass # Super admins see all
            elif getattr(user, 'role', None) in ['RESTAURANT', 'RESTAURANT_ADMIN']:
                queryset = queryset.filter(restaurant__user=user)
            else:
                queryset = queryset.none()
        else:
            # Auto-filter for restaurant owners if no specific ID requested
            if not restaurant_id and user.is_authenticated and getattr(user, 'role', None) in ['RESTAURANT', 'RESTAURANT_ADMIN']:
                queryset = queryset.filter(restaurant__user=user)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        
        # If Superadmin, rely on serializer data (which should include restaurant ID)
        if getattr(user, 'is_superuser', False) or getattr(user, 'role', None) == 'SUPERADMIN':
            serializer.save()
            return

        # If Restaurant Owner, enforce their restaurant
        if getattr(user, 'role', None) in ['RESTAURANT', 'RESTAURANT_ADMIN'] and isinstance(user, Users):
            restaurant = Restaurant.objects.filter(user=user).first()
            if not restaurant:
                raise permissions.exceptions.PermissionDenied("You do not have a registered restaurant profile.")
            serializer.save(restaurant=restaurant)
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

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        export_format = request.query_params.get('format', 'csv')
        food_resource = FoodItemResource()
        dataset = food_resource.export(self.get_queryset())
        
        if export_format == 'xlsx':
            response = HttpResponse(dataset.xlsx, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="food_items.xlsx"'
        elif export_format == 'xls':
            response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename="food_items.xls"'
        else:
            response = HttpResponse(dataset.csv, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="food_items.csv"'
        return response

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def import_csv(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=400)

        dataset = Dataset()
        # Decode the file contents and load it into the dataset
        try:
            file_extension = file.name.split('.')[-1].lower() if '.' in file.name else 'csv'
            if file_extension in ['xlsx', 'xls']:
                dataset.load(file.read(), format=file_extension)
            else:
                dataset.load(file.read().decode('utf-8'), format='csv')
        except Exception as e:
            return Response({"error": f"Failed to parse file: {str(e)}"}, status=400)
            
        user = request.user
        # Security: Enforce restaurant for non-superadmins
        if not (getattr(user, 'is_superuser', False) or getattr(user, 'role', None) == 'SUPERADMIN'):
            allowed_restaurant = Restaurant.objects.filter(user=user).first()
            if not allowed_restaurant:
                return Response({"error": "No restaurant associated with your account."}, status=400)
            
            # Force all imported rows to belong to this user's restaurant
            if 'restaurant' in dataset.headers:
                del dataset['restaurant']
            dataset.append_col([allowed_restaurant.name] * len(dataset), header='restaurant')
        
        food_resource = FoodItemResource()
        # dry_run=True tests the import for errors without saving to database
        result = food_resource.import_data(dataset, dry_run=True)
        
        if not result.has_errors():
            food_resource.import_data(dataset, dry_run=False) # Actual save
            return Response({"message": f"Successfully imported {len(dataset)} items."})
        else:
            errors = []
            for i, row_errors in enumerate(result.row_errors()):
                for error in row_errors[1]:
                    errors.append(f"Row {row_errors[0]}: {str(error.error)}")
            return Response({"error": "Import failed", "details": errors}, status=400)