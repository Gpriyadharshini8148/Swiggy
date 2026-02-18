from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from admin.restaurants.models.food_item import FoodItem
from admin.user.serializers import FoodItemSerializer

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def food_items_api(request):
    query = request.query_params.get('query')
    category_name = request.query_params.get('category')
    veg_only = request.query_params.get('veg_only')
    min_price = request.query_params.get('min_price')
    max_price = request.query_params.get('max_price')
    restaurant_id = request.query_params.get('restaurant_id')
    
    items = FoodItem.objects.filter(is_available=True, restaurant__is_active=True)
    
    if query:
        items = items.filter(name__icontains=query) | items.filter(description__icontains=query)
        items = items.distinct()
        
    if category_name:
        items = items.filter(category__name__icontains=category_name)
    
    sub_category_name = request.query_params.get('sub_category')
    if sub_category_name:
        items = items.filter(sub_category__name__icontains=sub_category_name)
        
    if veg_only and veg_only.lower() == 'true':
        items = items.filter(is_veg=True)
        
    if min_price:
        items = items.filter(price__gte=min_price)
    
    if max_price:
        items = items.filter(price__lte=max_price)
        
    if restaurant_id:
        items = items.filter(restaurant_id=restaurant_id)
        
    # Serialize
    serializer = FoodItemSerializer(items, many=True, context={'request': request})
    return Response(serializer.data)
