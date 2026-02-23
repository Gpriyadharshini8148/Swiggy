from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.restaurants.models import Restaurant
from admin.restaurants.serializers import RestaurantSerializer
from admin.restaurants.models import FoodItem
from admin.restaurants.serializers import FoodItemSerializer
from rest_framework.pagination import LimitOffsetPagination
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