from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from admin.access.models import Address, Users
from admin.access.serializers import AddressSerializer
from ..permissions import IsAuthenticatedUser

class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticatedUser]
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return Address.objects.all()
        user_id = self.request.session.get('user_id')
        if not user_id:
            return Address.objects.none()
        try:
            user = Users.objects.get(id=user_id)
            if user.role == 'ADMIN':
                return Address.objects.all()
            return Address.objects.filter(user_id=user_id)
        except Users.DoesNotExist:
            return Address.objects.none()

    @action(detail=False, methods=['get'], url_path='list-by-user')
    def list_by_user(self, request):
        user_id = request.query_params.get('user_id') or request.session.get('user_id')
        queryset = self.get_queryset().filter(user_id=user_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
