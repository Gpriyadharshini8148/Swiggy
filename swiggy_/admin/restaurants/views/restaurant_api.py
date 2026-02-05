from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.restaurants.models import Restaurant
from admin.restaurants.serializers import RestaurantSerializer

class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'category']

    @action(detail=True, methods=['get'])
    def menu(self, request, pk=None):
        restaurant = self.get_object()
        from admin.restaurants.models import FoodItem
        from admin.restaurants.serializers import FoodItemSerializer
        food_items = FoodItem.objects.filter(restaurant=restaurant)
        serializer = FoodItemSerializer(food_items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search_nearby(self, request):
        location = request.query_params.get('location')
        if not location:
            return Response({"error": "Location query parameter is required"}, status=400)
        restaurants = Restaurant.objects.filter(location__icontains=location)
        serializer = self.get_serializer(restaurants, many=True)
        return Response(serializer.data)
