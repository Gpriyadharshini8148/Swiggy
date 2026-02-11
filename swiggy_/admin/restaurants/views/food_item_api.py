from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.restaurants.models import FoodItem
from admin.restaurants.serializers import FoodItemSerializer

class FoodItemViewSet(viewsets.ModelViewSet):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemSerializer