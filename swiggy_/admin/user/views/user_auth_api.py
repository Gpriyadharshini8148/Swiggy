from admin.access.views.auth_view import AuthViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, permissions
from admin.access.models.address import Address
from admin.user.models.serviceable_zone import ServiceableZone
from admin.user.serializers import UserAddressSerializer, ServiceableZoneSerializer

class UserAuthViewSet(AuthViewSet):
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def set_location(self, request):
        try:
            from admin.access.models import Users
        except ImportError:
            pass
            
        user = request.user
        if not isinstance(user, Users):
             # Fallback: Try to find Users by username if request.user is a Django User
             try:
                 user = Users.objects.get(username=request.user.username)
             except Users.DoesNotExist:
                 return Response({"error": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserAddressSerializer(data=request.data)
        if serializer.is_valid():
            address = serializer.save(user=user)
            
            # Check serviceability
            lat = address.location.y if address.location else None
            lng = address.location.x if address.location else None
            
            if lat and lng:
                zones = ServiceableZone.objects.filter(is_active=True)
                serviceable_zone = None
                for zone in zones:
                    # Approximation: 1 degree latitude ~= 111 km
                    dist = ((float(zone.center_latitude) - float(lat))**2 + (float(zone.center_longitude) - float(lng))**2)**0.5 * 111
                    if dist <= float(zone.radius_km):
                        serviceable_zone = zone
                        break
                
                if serviceable_zone:
                    return Response({
                        "message": "Location set successfully. You are in a serviceable zone.",
                        "address": UserAddressSerializer(address).data,
                        "serviceable": True,
                        "zone": ServiceableZoneSerializer(serviceable_zone).data
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "message": "Location set, but it is outside our serviceable zones.",
                        "address": UserAddressSerializer(address).data,
                        "serviceable": False
                    }, status=status.HTTP_200_OK)
                    
            return Response({
                "message": "Location set successfully.",
                "address": UserAddressSerializer(address).data
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def get_addresses(self, request):
        try:
            from admin.access.models import Users
        except ImportError:
            pass
            
        if getattr(request.user, 'role', None) == 'SUPERADMIN' or getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_staff', False):
             addresses = Address.objects.all()
        elif isinstance(request.user, Users):
             addresses = Address.objects.filter(user=request.user)
        else:
             return Response({"error": "Valid User/User ID required for address access"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserAddressSerializer(addresses, many=True)
        return Response(serializer.data)
