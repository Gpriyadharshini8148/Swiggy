from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from admin.restaurants.models.review import Review
from admin.user.serializers import ReviewSerializer

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_review_api(request):
    data = request.data.copy()
    
    # 1. Validate Order
    order_id = data.get('order')
    if not order_id:
         return Response({"error": "Order ID is required"}, status=status.HTTP_400_BAD_REQUEST)

    from admin.delivery.models.orders import Orders
    try:
        order = Orders.objects.get(id=order_id)
    except Orders.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        
    if order.user != request.user:
        return Response({"error": "You can only review your own orders"}, status=status.HTTP_403_FORBIDDEN)
        
    if order.order_status != 'DELIVERED':
        return Response({"error": "You can only review delivered orders"}, status=status.HTTP_400_BAD_REQUEST)

    # 2. Add Restaurant and User to data if missing
    if 'restaurant' not in data:
        data['restaurant'] = order.restaurant.id
    elif int(data['restaurant']) != order.restaurant.id:
        return Response({"error": "Order does not match restaurant"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = ReviewSerializer(data=data)
    if serializer.is_valid():
        try:
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
             
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def restaurant_reviews_api(request, restaurant_id):
    reviews = Review.objects.filter(restaurant_id=restaurant_id).order_by('-created_at')
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data)
