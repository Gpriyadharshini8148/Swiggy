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
    if getattr(request.user, 'role', None) == 'SUPERADMIN':
        notifications = Notification.objects.all().order_by('-created_at')
    elif isinstance(request.user, Users):
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    else:
        return Response({"error": "Invalid user context"}, status=status.HTTP_400_BAD_REQUEST)
        
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read_api(request, notification_id):
    try:
        from admin.access.models import Users
    except ImportError:
        pass

    try:
        if getattr(request.user, 'role', None) == 'SUPERADMIN':
             notification = Notification.objects.get(id=notification_id)
        elif isinstance(request.user, Users):
             notification = Notification.objects.get(id=notification_id, user=request.user)
        else:
             return Response({"error": "Invalid user context"}, status=status.HTTP_400_BAD_REQUEST)

        notification.is_read = True
        notification.save()
        return Response({"message": "Marked as read"})
    except Notification.DoesNotExist:
        return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)