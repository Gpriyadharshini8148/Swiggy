from django.urls import path, include
from rest_framework.routers import DefaultRouter
from admin.restaurants.views import (
    RestaurantViewSet, 
    FoodItemViewSet, 
    CategoryViewSet, 
    SubCategoryViewSet,
    CouponViewSet, 
    CartViewSet,
    RestaurantDashboardViewSet 
)

router = DefaultRouter()
router.register(r'restaurants', RestaurantViewSet, basename='restaurants')
router.register(r'food-items', FoodItemViewSet, basename='food-items')
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'sub-categories', SubCategoryViewSet, basename='sub-categories')
router.register(r'coupons', CouponViewSet, basename='coupons')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'dashboard', RestaurantDashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
