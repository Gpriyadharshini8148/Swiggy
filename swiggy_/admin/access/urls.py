from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthViewSet
from rest_framework.decorators import api_view
from rest_framework.response import Response

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
@api_view(['GET'])
def auth_root(request):
    return Response({
        'login': request.build_absolute_uri('login/'),
        'signup': request.build_absolute_uri('signup/'),
        'verify-otp': request.build_absolute_uri('verify-otp/'),
        'logout': request.build_absolute_uri('logout/'),
    })

urlpatterns = [
    path('', auth_root, name='auth-root'),
    path('login/', AuthViewSet.as_view({'post': 'login'}), name='login'),
    path('signup/', AuthViewSet.as_view({'post': 'signup'}), name='signup'),
    path('verify-otp/', AuthViewSet.as_view({'post': 'verify_otp'}), name='verify-otp'),
    path('logout/', AuthViewSet.as_view({'post': 'logout'}), name='logout'),
]
