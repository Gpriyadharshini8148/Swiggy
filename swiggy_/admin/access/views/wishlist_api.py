from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.access.models import Wishlist, Users
from admin.restaurants.models import FoodItem
from admin.access.serializers import WishlistSerializer
from ..permissions import IsAuthenticatedUser
from django.utils import timezone

class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticatedUser]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            # Safely check is_superuser
            is_superuser = getattr(user, 'is_superuser', False)
            if getattr(user, 'role', None) == 'SUPER_ADMIN' or is_superuser:
                 return Wishlist.objects.all()
            if isinstance(user, Users):
                return Wishlist.objects.filter(user=user, deleted_at__isnull=True)
        
        user_id = self.request.session.get('user_id')
        if not user_id:
            return Wishlist.objects.none()
        return Wishlist.objects.filter(user__id=user_id, deleted_at__isnull=True)

    def _get_target_user_id(self, request):
        user = request.user
        if user.is_authenticated:
            # Safely check is_superuser as it might not be present on custom Users model
            is_superuser = getattr(user, 'is_superuser', False)
            if getattr(user, 'role', None) == 'SUPER_ADMIN' or is_superuser:
                # If Super Admin, allow specifying user_id in data. 
                # Do NOT fallback to user.id (which is Admin ID) as it won't match Users table.
                return request.data.get('user') or request.data.get('user_id')
            if isinstance(user, Users):
                return user.id
        return request.session.get('user_id')

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """
        Toggles an item in the wishlist:
        - If item exists (and not deleted), remove it (soft delete).
        - If item does not exist or is deleted, add/restore it.
        """
        user_id = self._get_target_user_id(request)
        if not user_id:
             return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
             
        food_item_id = request.data.get('food_item_id') or request.data.get('food_item')
        if not food_item_id:
            return Response({"error": "Food Item ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            food_item = FoodItem.objects.get(id=food_item_id)
            
            # Check for existing item (including soft deleted ones)
            wishlist_item = Wishlist.objects.filter(user_id=user_id, food_item=food_item).first()
            
            if wishlist_item:
                if wishlist_item.deleted_at:
                    # CASE: Restore (Add)
                    wishlist_item.deleted_at = None
                    wishlist_item.save()
                    return Response({"message": "Added to wishlist"}, status=status.HTTP_200_OK)
                else:
                    # CASE: Remove (Soft delete)
                    wishlist_item.deleted_at = timezone.now()
                    wishlist_item.save()
                    return Response({"message": "Removed from wishlist"}, status=status.HTTP_200_OK)
            else:
                # CASE: Create new
                wishlist_item = Wishlist.objects.create(
                    user_id=user_id, 
                    food_item=food_item,
                    deleted_at=None
                )
                return Response({"message": "Added to wishlist"}, status=status.HTTP_201_CREATED)

        except FoodItem.DoesNotExist:
             return Response({"error": "Food Item not found"}, status=status.HTTP_404_NOT_FOUND)
