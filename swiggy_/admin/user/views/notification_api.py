from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from admin.user.models.notification import Notification
from admin.user.serializers import NotificationSerializer
from admin.access.models import Users

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def push_notification_api(request):
    if getattr(request.user, 'role', None) == 'SUPERADMIN':
        return Response({"error": "Admins cannot receive push notifications"}, status=status.HTTP_400_BAD_REQUEST)
        
    # Ensure user is a Users instance
    if not isinstance(request.user, Users):
        return Response({"error": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = NotificationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_notifications_api(request):
    notifications = Notification.objects.none()
    
    # Safely check for is_superuser
    is_superuser = getattr(request.user, 'is_superuser', False)
    
    if getattr(request.user, 'role', None) == 'SUPER_ADMIN' or is_superuser:
        notifications = Notification.objects.all().order_by('-created_at')
    elif isinstance(request.user, Users):
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    else:
        # Fallback for unexpected user types
        notifications = Notification.objects.none()
        
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_notification_detail_api(request, pk):
    try:
        if getattr(request.user, 'role', None) == 'SUPER_ADMIN' or getattr(request.user, 'is_superuser', False):
             notification = Notification.objects.get(id=pk)
        elif isinstance(request.user, Users):
             notification = Notification.objects.get(id=pk, user=request.user)
        else:
             return Response({"error": "Invalid user context"}, status=status.HTTP_400_BAD_REQUEST)

        # Mark as read specific notification
        if not notification.is_read:
            notification.is_read = True
            notification.save()

        serializer = NotificationSerializer(notification)
        return Response(serializer.data)
    except Notification.DoesNotExist:
        return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)