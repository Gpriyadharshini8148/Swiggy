from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from admin.restaurants.models.restaurant import Restaurant
from admin.restaurants.models.food_item import FoodItem
from admin.restaurants.models.category import Category, SubCategory
from collections import defaultdict
from admin.user.serializers import RestaurantListSerializer, FoodItemSerializer, CategorySerializer, SubCategorySerializer

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_restaurants_api(request):
    lat = request.query_params.get('lat')
    lng = request.query_params.get('lng')
    restaurants = Restaurant.objects.filter(is_active=True)
    cuisine = request.query_params.get('cuisine')
    if cuisine:
        restaurants = restaurants.filter(fooditem__category__name__icontains=cuisine).distinct()
    min_rating = request.query_params.get('min_rating')
    if min_rating:
        restaurants = restaurants.filter(rating__gte=min_rating)
    
    # Pass lat/lng to serializer context for distance calculation
    serializer = RestaurantListSerializer(restaurants, many=True, context={'lat': lat, 'lng': lng, 'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def restaurant_menu_api(request, restaurant_id):
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
        
        # Recommended Items (Logic: Top rated or just first 5 available items for now as no rating/order count exists on item)
        # Using slice for simple recommendation mock
        recommended_items = FoodItem.objects.filter(restaurant=restaurant, is_available=True)[:5]
        
        # Group menu by category and subcategory
        categories = Category.objects.filter(fooditem__restaurant=restaurant).distinct()
        
        menu_data = []
        for category in categories:
            category_data = {
                "category": CategorySerializer(category).data,
                "sub_categories": []
            }
            
            # Get subcategories for this category that have items in this restaurant
            # Or just filter items by category and then group by subcategory
            # Strategy: Get all items for this category in this restaurant
            items_in_cat = FoodItem.objects.filter(restaurant=restaurant, category=category)
            
            # Group by subcategory
            subcat_map = defaultdict(list)
            for item in items_in_cat:
                sub_cat_key = item.sub_category
                subcat_map[sub_cat_key].append(item)
            
            for sub_cat, items in subcat_map.items():
                # sub_cat is a SubCategory object or None
                sub_cat_data = {
                    "sub_category": SubCategorySerializer(sub_cat).data if sub_cat else None,
                    "items": FoodItemSerializer(items, many=True, context={'request': request}).data
                }
                category_data["sub_categories"].append(sub_cat_data)
            
            menu_data.append(category_data)
            
        response_data = {
            "restaurant": RestaurantListSerializer(restaurant, context={'lat': request.query_params.get('lat'), 'lng': request.query_params.get('lng'), 'request': request}).data,
            "recommended_items": FoodItemSerializer(recommended_items, many=True, context={'request': request}).data,
            "menu": menu_data
        }
            
        return Response(response_data)
    except Restaurant.DoesNotExist:
        return Response({"error": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND)
