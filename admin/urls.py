from django.urls import path, include
from rest_framework.routers import DefaultRouter
from admin.users.views import UsersViewSet, AddressViewSet, WishlistViewSet, RewardsViewSet
from admin.access.views import AuthViewSet
from admin.restaurants.views import RestaurantViewSet, CategoryViewSet, FoodItemViewSet, CartViewSet, CouponViewSet
from admin.delivery.views import OrdersViewSet, DeliveryPartnerViewSet
from django.views.generic import RedirectView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'users', UsersViewSet, basename='users')
router.register(r'address', AddressViewSet, basename='address')
router.register(r'wishlist', WishlistViewSet, basename='wishlist')
router.register(r'rewards', RewardsViewSet, basename='rewards')
router.register(r'restaurants', RestaurantViewSet, basename='restaurants')
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'fooditems', FoodItemViewSet, basename='fooditems')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'coupons', CouponViewSet, basename='coupons')
router.register(r'orders', OrdersViewSet, basename='orders')
router.register(r'delivery-partners', DeliveryPartnerViewSet, basename='delivery-partners')

schema_view = get_schema_view(
   openapi.Info(
      title="Swiggy API",
      default_version='v1',
      description="API documentation for Swiggy",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email=["gpriyadharshini9965@gmail.com"]),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', RedirectView.as_view(url='api/', permanent=False)),
    path('api/', include(router.urls)),
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]