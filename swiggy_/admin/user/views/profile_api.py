from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from admin.access.models.users import Users
from admin.user.serializers import UserProfileSerializer

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile_api(request):
    try:
        # Ensure we have the correct Users instance
        user = request.user
        if not isinstance(user, Users):
            # Assuming username links them
            try:
                user = Users.objects.get(username=request.user.username)
            except Users.DoesNotExist:
                return Response({"error": f"User profile not found for user: {request.user.username}"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
