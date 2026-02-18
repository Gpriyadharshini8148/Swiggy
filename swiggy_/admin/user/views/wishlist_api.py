from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.access.models import Wishlist, Users
from admin.restaurants.models import FoodItem
from admin.user.serializers import WishlistSerializer
from django.utils import timezone

class UserWishlistViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def _get_target_user(self, request):
        # Similar safe user handling as in Cart API
        user = request.user
        if isinstance(user, Users):
            return user
        if user.is_authenticated:
            try:
                return Users.objects.get(id=user.id)
            except Users.DoesNotExist:
                pass
        return None

    @action(detail=False, methods=['get'])
    def my_wishlist(self, request):
        user = self._get_target_user(request)
        if not user:
            return Response({"error": "User not found or not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
            
        wishlist_items = Wishlist.objects.filter(user=user, deleted_at__isnull=True)
        # We need a serializer that likely includes Food Item details
        # Let's assume WishlistSerializer from admin.user.serializers or admin.access.serializers
        serializer = WishlistSerializer(wishlist_items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        user = self._get_target_user(request)
        if not user:
             return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
             
        restaurant_id = request.data.get('restaurant_id') or request.data.get('restaurant')
        if not restaurant_id:
            return Response({"error": "Restaurant ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            from admin.restaurants.models import Restaurant
            restaurant = Restaurant.objects.get(id=restaurant_id)
            
            # Check for existing item (including soft deleted ones)
            wishlist_item = Wishlist.objects.filter(user=user, restaurant=restaurant).first()
            
            if wishlist_item:
                if wishlist_item.deleted_at:
                    # CASE: Restore (Add)
                    wishlist_item.deleted_at = None
                    wishlist_item.save()
                    return Response({"message": f"{restaurant.name} added to wishlist"}, status=status.HTTP_200_OK)
                else:
                    # CASE: Remove (Soft delete)
                    wishlist_item.deleted_at = timezone.now()
                    wishlist_item.save()
                    return Response({"message": f"{restaurant.name} removed from wishlist"}, status=status.HTTP_200_OK)
            else:
                # CASE: Create new
                wishlist_item = Wishlist.objects.create(
                    user=user, 
                    restaurant=restaurant,
                    deleted_at=None
                )
                return Response({"message": f"{restaurant.name} added to wishlist"}, status=status.HTTP_201_CREATED)

        except Restaurant.DoesNotExist:
             return Response({"error": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND)
