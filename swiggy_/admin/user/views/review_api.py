from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from admin.restaurants.models.review import Review
from admin.user.serializers import ReviewSerializer

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_review_api(request):
    serializer = ReviewSerializer(data=request.data)
    if serializer.is_valid():
        # Ensure user can only review orders they placed
        # This check could be added if order_id is provided in serializer
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def restaurant_reviews_api(request, restaurant_id):
    reviews = Review.objects.filter(restaurant_id=restaurant_id).order_by('-created_at')
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data)
