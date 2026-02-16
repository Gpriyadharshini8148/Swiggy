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
            if getattr(user, 'role', None) == 'SUPERADMIN' or user.is_superuser:
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
            if getattr(user, 'role', None) == 'SUPERADMIN' or user.is_superuser:
                # If Super Admin, allow specifying user_id in data. 
                # Do NOT fallback to user.id (which is Admin ID) as it won't match Users table.
                return request.data.get('user') or request.data.get('user_id')
            if isinstance(user, Users):
                return user.id
        return request.session.get('user_id')

    @action(detail=False, methods=['post'])
    def add_to_wishlist(self, request):
        user_id = self._get_target_user_id(request)
        food_item_id = request.data.get('food_item_id') or request.data.get('food_item')
        if not user_id:
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        if not food_item_id:
            return Response({"error": "Food Item ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            food_item = FoodItem.objects.get(id=food_item_id)
            wishlist_item, created = Wishlist.objects.get_or_create(
                user_id=user_id,
                food_item=food_item,
                defaults={'deleted_at': None}
            )
            if not created and wishlist_item.deleted_at:
                wishlist_item.deleted_at = None
                wishlist_item.save()
            return Response({"message": "Added to wishlist", "id": wishlist_item.id}, status=status.HTTP_201_CREATED)
        except FoodItem.DoesNotExist:
            return Response({"error": "Food Item not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def remove_from_wishlist(self, request):
        user_id = self._get_target_user_id(request)
        food_item_id = request.data.get('food_item_id')
        wishlist_id = request.data.get('wishlist_id')
        if not user_id:
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            if wishlist_id:
                item = Wishlist.objects.get(id=wishlist_id, user_id=user_id)
            elif food_item_id:
                item = Wishlist.objects.get(food_item_id=food_item_id, user_id=user_id, deleted_at__isnull=True)
            else:
                return Response({"error": "Wishlist ID or Food Item ID required"}, status=status.HTTP_400_BAD_REQUEST)
            item.deleted_at = timezone.now()
            item.save()
            return Response({"message": "Removed from wishlist"})
        except Wishlist.DoesNotExist:
            return Response({"error": "Item not found in wishlist"}, status=status.HTTP_404_NOT_FOUND)
