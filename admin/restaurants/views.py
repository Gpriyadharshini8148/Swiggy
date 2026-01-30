from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Restaurant, FoodItem, Cart, CartItem, Category, Coupon
from .serializers import RestaurantSerializer, FoodItemSerializer, CartSerializer, CartItemSerializer, CategorySerializer, CouponSerializer

class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'category']

    @action(detail=True, methods=['get'])
    def menu(self, request, pk=None):
        pass
    
    @action(detail=False, methods=['get'])
    def search_nearby(self, request):
        pass

class FoodItemViewSet(viewsets.ModelViewSet):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemSerializer

    @action(detail=True, methods=['get'])
    def customizations(self, request, pk=None):
        pass

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    @action(detail=False, methods=['get'])
    def my_cart(self, request):
        pass

    @action(detail=False, methods=['post'])
    def clear_cart(self, request):
        pass

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        pass
