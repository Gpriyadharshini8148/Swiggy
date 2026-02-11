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
        serializer = UserAddressSerializer(data=request.data)
        if serializer.is_valid():
            address = serializer.save(user=request.user)
            
            # Check serviceability
            lat = address.latitude
            lng = address.longitude
            
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
        addresses = Address.objects.filter(user=request.user)
        serializer = UserAddressSerializer(addresses, many=True)
        return Response(serializer.data)
