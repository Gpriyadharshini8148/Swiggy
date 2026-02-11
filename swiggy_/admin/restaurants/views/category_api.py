from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.restaurants.models import Category, SubCategory, Restaurant, FoodItem
from admin.restaurants.serializers import CategorySerializer, SubCategorySerializer, RestaurantSerializer, FoodItemSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def perform_create(self, serializer):
        name = serializer.validated_data.get('name')
        if Category.objects.filter(name__iexact=name).exists():
             pass
        serializer.save()

    @action(detail=True, methods=['get'])
    def restaurants(self, request, pk=None):
        category = self.get_object()
        restaurants = Restaurant.objects.filter(category__icontains=category.name)
        serializer = RestaurantSerializer(restaurants, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def food_items(self, request, pk=None):
        category = self.get_object()
        food_items = FoodItem.objects.filter(category=category)
        serializer = FoodItemSerializer(food_items, many=True)
        return Response(serializer.data)

class SubCategoryViewSet(viewsets.ModelViewSet):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
