from rest_framework import viewsets
from admin.restaurants.models import Category
from admin.restaurants.serializers import CategorySerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
