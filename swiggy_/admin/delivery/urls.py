from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrdersViewSet, DeliveryPartnerViewSet, RazorpayPaymentViewSet
from rest_framework.decorators import api_view
from rest_framework.response import Response

router = DefaultRouter()
router.register(r'orders', OrdersViewSet, basename='orders')
router.register(r'delivery-partners', DeliveryPartnerViewSet, basename='delivery-partners')
router.register(r'payments', RazorpayPaymentViewSet, basename='payments')

@api_view(['GET'])
def delivery_root(request):
    return Response({
        'orders': request.build_absolute_uri('orders/'),
        'delivery-partners': request.build_absolute_uri('delivery-partners/'),
        'place-order': request.build_absolute_uri('place-order/'),
    })

urlpatterns = [
    path('', delivery_root, name='delivery-root'),
    path('', include(router.urls)),
    path('place-order/', OrdersViewSet.as_view({'post': 'place_order'}), name='place-order'),
]
