from rest_framework import viewsets
from admin.restaurants.models import Coupon
from admin.restaurants.serializers import CouponSerializer

class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
