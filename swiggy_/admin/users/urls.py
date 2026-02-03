from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UsersViewSet, AddressViewSet, WishlistViewSet, RewardsViewSet

router = DefaultRouter()
router.register(r'', UsersViewSet, basename='users')
router.register(r'address', AddressViewSet, basename='address')
router.register(r'wishlist', WishlistViewSet, basename='wishlist')
router.register(r'rewards', RewardsViewSet, basename='rewards')

urlpatterns = [
    path('', include(router.urls)),
]
