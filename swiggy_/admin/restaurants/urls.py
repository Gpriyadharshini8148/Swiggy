from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RestaurantViewSet, CategoryViewSet, FoodItemViewSet, CartViewSet, CouponViewSet

router = DefaultRouter()
router.register(r'', RestaurantViewSet, basename='restaurants')
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'fooditems', FoodItemViewSet, basename='fooditems')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'coupons', CouponViewSet, basename='coupons')

urlpatterns = [
    path('', include(router.urls)),
]
