from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from admin.access.models import Images
from admin.access.serializers import ImagesSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(
    method='post',
    request_body=ImagesSerializer,
    responses={201: ImagesSerializer, 400: 'Bad Request'}
)
@api_view(['POST'])
@permission_classes([AllowAny]) # Or IsAuthenticated based on requirements, assuming AllowAny for now as per minimal info
def upload_image_api(request):
    """
    API endpoint to upload an image.
    """
    serializer = ImagesSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get',
    responses={200: ImagesSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_images_api(request):
    """
    API endpoint to list all images.
    """
    images = Images.objects.all()
    serializer = ImagesSerializer(images, many=True)
    return Response(serializer.data)
