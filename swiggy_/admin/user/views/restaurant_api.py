from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from admin.restaurants.models.restaurant import Restaurant
from admin.restaurants.models.food_item import FoodItem
from admin.restaurants.models.category import Category
from admin.user.serializers import RestaurantListSerializer, FoodItemSerializer, CategorySerializer

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_restaurants_api(request):
    lat = request.query_params.get('lat')
    lng = request.query_params.get('lng')
    
    # In a real app, filter by distance using lat/lng
    restaurants = Restaurant.objects.filter(is_active=True)
    
    # Filter by cuisine, rating, etc.
    cuisine = request.query_params.get('cuisine')
    if cuisine:
        restaurants = restaurants.filter(fooditem__category__name__icontains=cuisine).distinct()
        
    min_rating = request.query_params.get('min_rating')
    if min_rating:
        restaurants = restaurants.filter(rating__gte=min_rating)
        
    serializer = RestaurantListSerializer(restaurants, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def restaurant_menu_api(request, restaurant_id):
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
        # Group menu by category
        categories = Category.objects.filter(fooditem__restaurant=restaurant).distinct()
        
        response_data = []
        for category in categories:
            items = FoodItem.objects.filter(restaurant=restaurant, category=category)
            response_data.append({
                "category": CategorySerializer(category).data,
                "items": FoodItemSerializer(items, many=True).data
            })
            
        return Response(response_data)
    except Restaurant.DoesNotExist:
        return Response({"error": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND)
