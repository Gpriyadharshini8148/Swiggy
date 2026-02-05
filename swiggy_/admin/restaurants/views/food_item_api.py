from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.restaurants.models import FoodItem
from admin.restaurants.serializers import FoodItemSerializer

class FoodItemViewSet(viewsets.ModelViewSet):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemSerializer

    @action(detail=True, methods=['get'])
    def customizations(self, request, pk=None):
        food_item = self.get_object()
        return Response({
            "food_item": food_item.name,
            "customizations": food_item.customization or {}
        })
