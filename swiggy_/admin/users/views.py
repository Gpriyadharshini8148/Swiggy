from rest_framework import viewsets,status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Users,Address,Wishlist,Rewards
from .serializers import UsersSerializer,AddressSerializer,WishlistSerializer,RewardsSerializer
from admin.access.permissions import IsSuperAdmin,IsAuthenticatedUser
from admin.restaurants.models import FoodItem
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.db.models import Sum
class UsersViewSet(viewsets.ModelViewSet):
    queryset=Users.objects.all()
    serializer_class=UsersSerializer

    def get_permissions(self):
        if self.action=='list':
            return [IsSuperAdmin()]
        elif self.action in ['create','register','login']:
            return []
        else:
            return [IsAuthenticatedUser()]
    def get_queryset(self):
        if self.request.user.is_superuser:
            return Users.objects.all()
        user_id=self.request.session.get('user_id')
        if not user_id:
            return Users.objects.none()
        try:
            current_user=Users.objects.get(id=user_id)
            if current_user.role=='ADMIN':
                return Users.objects.all()
            else:
                return Users.objects.filter(id=user_id)
        except Users.DoesNotExist:
            return Users.objects.none()

    @action(detail=False,methods=['post'])
    def login(self,request):
        return Response({"message":"Use /access/auth/verify_otp/ for login"})

    @action(detail=False,methods=['post'])
    def register(self,request):
        data=request.data.copy()
        password=data.pop('password',None)
        if password:
            data['password_hash']=make_password(password)
        serializer=self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,methods=['get'])
    def profile(self,request,pk=None):
        instance=self.get_object()
        serializer=self.get_serializer(instance)
        return Response(serializer.data)

class AddressViewSet(viewsets.ModelViewSet):
    queryset=Address.objects.all()
    serializer_class=AddressSerializer
    permission_classes=[IsAuthenticatedUser]
    def get_queryset(self):
        if self.request.user.is_superuser:
            return Address.objects.all()
        user_id=self.request.session.get('user_id')
        if not user_id:
            return Address.objects.none()
        try:
            user=Users.objects.get(id=user_id)
            if user.role=='ADMIN':
                return Address.objects.all()
            return Address.objects.filter(user_id=user_id)
        except Users.DoesNotExist:
            return Address.objects.none()

    @action(detail=False,methods=['get'],url_path='list-by-user')
    def list_by_user(self,request):
        user_id=request.query_params.get('user_id') or request.session.get('user_id')
        queryset=self.get_queryset().filter(user_id=user_id)
        serializer=self.get_serializer(queryset,many=True)
        return Response(serializer.data)

class WishlistViewSet(viewsets.ModelViewSet):
    queryset=Wishlist.objects.all()
    serializer_class=WishlistSerializer
    permission_classes=[IsAuthenticatedUser]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Wishlist.objects.all()
        user_id=self.request.session.get('user_id')
        if not user_id:
            return Wishlist.objects.none()
        return Wishlist.objects.filter(user__id=user_id,deleted_at__isnull=True)

    @action(detail=False,methods=['post'])
    def add_to_wishlist(self,request):
        user_id=request.session.get('user_id')
        food_item_id=request.data.get('food_item_id')
        if not user_id:
            return Response({"error":"User not authenticated"},status=status.HTTP_401_UNAUTHORIZED)
        if not food_item_id:
            return Response({"error":"Food Item ID is required"},status=status.HTTP_400_BAD_REQUEST)
        try:
            food_item=FoodItem.objects.get(id=food_item_id)
            wishlist_item,created=Wishlist.objects.get_or_create(
                user_id=user_id,
                food_item=food_item,
                defaults={'deleted_at':None}
            )
            if not created and wishlist_item.deleted_at:
                wishlist_item.deleted_at=None
                wishlist_item.save()
            return Response({"message":"Added to wishlist","id":wishlist_item.id},status=status.HTTP_201_CREATED)
        except FoodItem.DoesNotExist:
            return Response({"error":"Food Item not found"},status=status.HTTP_404_NOT_FOUND)

    @action(detail=False,methods=['post'])
    def remove_from_wishlist(self,request):
        user_id=request.session.get('user_id')
        food_item_id=request.data.get('food_item_id')
        wishlist_id=request.data.get('wishlist_id')
        if not user_id:
            return Response({"error":"User not authenticated"},status=status.HTTP_401_UNAUTHORIZED)
        try:
            if wishlist_id:
                item=Wishlist.objects.get(id=wishlist_id,user_id=user_id)
            elif food_item_id:
                item=Wishlist.objects.get(food_item_id=food_item_id,user_id=user_id,deleted_at__isnull=True)
            else:
                return Response({"error":"Wishlist ID or Food Item ID required"},status=status.HTTP_400_BAD_REQUEST)
            item.deleted_at=timezone.now()
            item.save()
            return Response({"message":"Removed from wishlist"})
        except Wishlist.DoesNotExist:
            return Response({"error":"Item not found in wishlist"},status=status.HTTP_404_NOT_FOUND)

class RewardsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=Rewards.objects.all()
    serializer_class=RewardsSerializer
    permission_classes=[IsAuthenticatedUser]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Rewards.objects.all()
        user_id=self.request.session.get('user_id')
        if not user_id:
            return Rewards.objects.none()
        return Rewards.objects.filter(user_id=user_id)

    @action(detail=False,methods=['get'])
    def balance(self,request):
        user_id=request.session.get('user_id')
        if not user_id:
            return Response({"error":"User not authenticated"},status=status.HTTP_401_UNAUTHORIZED)
        rewards=Rewards.objects.filter(user_id=user_id)
        earned=rewards.aggregate(Sum('points_earned'))['points_earned__sum'] or 0
        redeemed=rewards.aggregate(Sum('points_redeemed'))['points_redeemed__sum'] or 0
        balance=earned-redeemed
        return Response({"balance":balance,"earned":earned,"redeemed":redeemed})

    @action(detail=False,methods=['post'])
    def redeem(self,request):
        user_id=request.session.get('user_id')
        points=request.data.get('points')
        if not user_id:
            return Response({"error":"User not authenticated"},status=status.HTTP_401_UNAUTHORIZED)
        if not points:
            return Response({"error":"Points amount required"},status=status.HTTP_400_BAD_REQUEST)
        try:
            points=int(points)
            if points<=0:
                return Response({"error":"Points must be positive"},status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error":"Invalid points value"},status=status.HTTP_400_BAD_REQUEST)
        rewards=Rewards.objects.filter(user_id=user_id)
        earned=rewards.aggregate(Sum('points_earned'))['points_earned__sum'] or 0
        redeemed=rewards.aggregate(Sum('points_redeemed'))['points_redeemed__sum'] or 0
        balance=earned-redeemed
        if points>balance:
            return Response({"error":"Insufficient balance","current_balance":balance},status=status.HTTP_400_BAD_REQUEST)
        Rewards.objects.create(user_id=user_id,points_redeemed=points,points_earned=0)
        return Response({"message":"Redeemed successfully","redeemed_points":points,"new_balance":balance-points})
