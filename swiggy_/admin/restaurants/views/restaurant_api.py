from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.restaurants.models import Restaurant
from admin.restaurants.serializers import RestaurantSerializer
from admin.restaurants.models import FoodItem
from admin.restaurants.serializers import FoodItemSerializer
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import MultiPartParser
from django.http import HttpResponse
from tablib import Dataset
from admin.restaurants.admin import RestaurantResource
from admin.access.models import Users
class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'category']

    @action(detail=True, methods=['get'])
    def menu_detail(self, request, pk=None):
        restaurant = self.get_object()
        
        # Check if restaurant is open
        if not restaurant.is_open:
             # Check if it's inactive (admin block) or just closed (out of hours)
             reason = "Restaurant is closed (After Hours)"
             if not restaurant.is_active:
                  reason = "Restaurant is currently inactive"
             return Response({"error": reason, "is_active": False, "menu": []}, status=status.HTTP_200_OK)

        food_items = FoodItem.objects.filter(restaurant=restaurant, is_available=True)
        serializer = FoodItemSerializer(food_items, many=True)
        return Response(serializer.data)
    @action(detail=False, methods=['get'])
    def search_nearby(self, request):
        location = request.query_params.get('location') or request.query_params.get('search')
        if not location:
            return Response({"error": "Location or search query parameter is required"}, status=400)
        restaurants = Restaurant.objects.filter(location__icontains=location)
        serializer = self.get_serializer(restaurants, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        user = request.user
        role = getattr(user, 'role', None)

        if getattr(user, 'is_superuser', False) or role == 'SUPERADMIN':
            queryset = Restaurant.objects.all()
        elif role in ['RESTAURANT', 'RESTAURANT_ADMIN']:
            queryset = Restaurant.objects.filter(user=user)
        else:
            return Response({"error": "Permission denied."}, status=403)

        resource = RestaurantResource()
        dataset = resource.export(queryset)
        
        export_format = request.query_params.get('format', 'csv')
        if export_format == 'xlsx':
            response = HttpResponse(dataset.xlsx, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="restaurants.xlsx"'
        elif export_format == 'xls':
            response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename="restaurants.xls"'
        else:
            response = HttpResponse(dataset.csv, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="restaurants.csv"'
        return response

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def import_csv(self, request):
        user = request.user
        role = getattr(user, 'role', None)
        
        if not (getattr(user, 'is_superuser', False) or role in ['SUPERADMIN', 'RESTAURANT', 'RESTAURANT_ADMIN']):
            return Response({"error": "Permission denied."}, status=403)

        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=400)

        dataset = Dataset()
        try:
            file_extension = file.name.split('.')[-1].lower() if '.' in file.name else 'csv'
            if file_extension in ['xlsx', 'xls']:
                dataset.load(file.read(), format=file_extension)
            else:
                dataset.load(file.read().decode('utf-8'), format='csv')
        except Exception as e:
            return Response({"error": f"Failed to parse file: {str(e)}"}, status=400)
            
        # Security: Enforce restaurant user for non-superadmins
        if not (getattr(user, 'is_superuser', False) or role == 'SUPERADMIN'):
            if 'user' in dataset.headers:
                del dataset['user']
            # Force all imported rows to belong to this user
            dataset.append_col([user.id] * len(dataset), header='user')
        
        resource = RestaurantResource()
        result = resource.import_data(dataset, dry_run=True)
        
        if not result.has_errors():
            resource.import_data(dataset, dry_run=False)
            return Response({"message": f"Successfully imported {len(dataset)} restaurants."})
        else:
            errors = []
            for i, row_errors in enumerate(result.row_errors()):
                for error in row_errors[1]:
                    errors.append(f"Row {row_errors[0]}: {str(error.error)}")
            return Response({"error": "Import failed", "details": errors}, status=400)