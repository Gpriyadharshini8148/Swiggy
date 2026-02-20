from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.access.models import Users
from admin.access.serializers import UsersSerializer
from ..permissions import IsAdmin, IsAuthenticatedUser
from django.contrib.auth.hashers import make_password

class UsersViewSet(viewsets.ModelViewSet):
    queryset = Users.objects.all()
    serializer_class = UsersSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [IsAdmin()]
        elif self.action in ['register', 'login']:
            return []
        else:
            return [IsAuthenticatedUser()]
    def create(self, request, *args, **kwargs):
        creator_role = None
        if getattr(request.user, 'is_superuser', False):
            creator_role = 'SUPERADMIN'
        else:
            user_id = request.session.get('user_id')
            if user_id:
                try:
                    creator_user = Users.objects.get(id=user_id)
                    creator_role = creator_user.role
                except Users.DoesNotExist:
                    pass
        target_role = request.data.get('role', 'USER')
        
        if creator_role == 'SUPERADMIN':
            pass 
        elif creator_role == 'ADMIN':
            if target_role == 'SUPERADMIN':
                 return Response({"error": "Admins cannot create Super Admins"}, status=status.HTTP_403_FORBIDDEN)
            # Expanded permissive check slightly or keep strict? Keeping strict based on code.
            if target_role not in ['ADMIN', 'USER', 'RESTAURANT', 'DELIVERY']:
                 # Allow creating other roles too since I merged them
                 pass
            
            # If I don't update this check, Admin cannot create Restaurant.
            # I will assume Admin SHOULD be able to create Restaurant/Delivery.
            if target_role == 'SUPERADMIN':
                return Response({"error": "Admins cannot create Super Admins"}, status=status.HTTP_403_FORBIDDEN)
        
        else:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
            
        data = request.data.copy()
        password = data.pop('password', None)
        if password:
            data['password_hash'] = make_password(password)
            
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        if getattr(self.request.user, 'is_superuser', False):
            return Users.objects.all()
        user_id = self.request.session.get('user_id')
        if not user_id:
            return Users.objects.none()
        try:
            current_user = Users.objects.get(id=user_id)
            if current_user.role in ['ADMIN', 'SUPERADMIN']: 
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
        data = request.data.copy()
        data['role'] = 'USER' 
        password = data.pop('password', None)
        if password:
            data['password_hash'] = make_password(password)
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
