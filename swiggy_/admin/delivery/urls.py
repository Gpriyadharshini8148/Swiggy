from django.urls import path, include
from rest_framework.routers import DefaultRouter
from admin.delivery.views import OrdersViewSet, DeliveryPartnerViewSet

router = DefaultRouter()
router.register(r'orders', OrdersViewSet, basename='orders')
router.register(r'delivery-partners', DeliveryPartnerViewSet, basename='delivery-partners')

urlpatterns = [
    path('', include(router.urls)),
]
