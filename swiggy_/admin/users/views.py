from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Users, Address, Wishlist, Rewards
from .serializers import UsersSerializer, AddressSerializer, WishlistSerializer, RewardsSerializer
from admin.access.permissions import IsSuperAdmin, IsAuthenticatedUser

class UsersViewSet(viewsets.ModelViewSet):
    queryset = Users.objects.all()
    serializer_class = UsersSerializer
    
    def get_permissions(self):
        if self.action == 'list':
            return [IsSuperAdmin()]
        elif self.action in ['create', 'register', 'login']:
            return []
        else:
            return [IsAuthenticatedUser()]

    def get_queryset(self):
        user_id = self.request.session.get('user_id')
        if not user_id:
            return Users.objects.none()
        try:
            current_user = Users.objects.get(id=user_id)
            if current_user.role == 'ADMIN':
                return Users.objects.all()
            else:
                return Users.objects.filter(id=user_id)
        except Users.DoesNotExist:
            return Users.objects.none()

    @action(detail=False, methods=['post'])
    def login(self, request):
        return Response({"message": "Use /access/auth/verify_otp/ for login"})

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticatedUser]
    
    def get_queryset(self):
        user_id = self.request.session.get('user_id')
        if not user_id:
             return Address.objects.none()
        user = Users.objects.get(id=user_id)
        if user.role == 'ADMIN':
            return Address.objects.all()
        return Address.objects.filter(user_id=user_id)

    def list_by_user(self, request, user_id=None):
        queryset = self.get_queryset().filter(user_id=user_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticatedUser]

    @action(detail=False, methods=['post'])
    def add_to_wishlist(self, request):
        pass

    @action(detail=False, methods=['post'])
    def remove_from_wishlist(self, request):
        pass

class RewardsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Rewards.objects.all()
    serializer_class = RewardsSerializer
    permission_classes = [IsAuthenticatedUser]

    @action(detail=True, methods=['post'])
    def redeem(self, request, pk=None):
        pass
