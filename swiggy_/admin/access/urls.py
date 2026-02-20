from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthViewSet, UsersViewSet, AddressViewSet, WishlistViewSet, RewardsViewSet, StateViewSet, CityViewSet, upload_image_api, list_images_api
from rest_framework.decorators import api_view
from rest_framework.response import Response

router = DefaultRouter()
router.register(r'account_creation_by_super_admin', AuthViewSet, basename='auth')
router.register(r'users', UsersViewSet, basename='users')
router.register(r'address', AddressViewSet, basename='address')
router.register(r'wishlist', WishlistViewSet, basename='wishlist')
router.register(r'rewards', RewardsViewSet, basename='rewards')
router.register(r'states', StateViewSet, basename='states')
router.register(r'cities', CityViewSet, basename='cities')

@api_view(['GET'])
def auth_root(request):
    urls = {
        'login': request.build_absolute_uri('login/'),
        'verify-otp': request.build_absolute_uri('verify-otp/'),
        'logout': request.build_absolute_uri('logout/'),
    }

    is_super_admin = False
    if request.user and request.user.is_authenticated:
        if getattr(request.user, 'is_superuser', False):
            is_super_admin = True
        elif getattr(request.user, 'role', None) == 'SUPERADMIN':
            is_super_admin = True
            
    if is_super_admin:
        urls['create-account-by-super-admin'] = request.build_absolute_uri('create_account_by_super_admin/')
        
    return Response(urls)

urlpatterns = [
    path('', auth_root, name='auth-root'),
    path('', include(router.urls)),
    path('login/', AuthViewSet.as_view({'post': 'login'}), name='login'),
    path('signup/', AuthViewSet.as_view({'post': 'signup'}), name='signup'),
    path('verify-otp/', AuthViewSet.as_view({'post': 'verify_otp'}), name='verify-otp'),
    path('create_account_by_super_admin/', AuthViewSet.as_view({'post': 'create_account_by_super_admin'}), name='create-account-by-super-admin'),
    path('restaurant_signup/', AuthViewSet.as_view({'post': 'restaurant_signup'}), name='restaurant-signup'),
    path('logout/', AuthViewSet.as_view({'post': 'logout'}), name='logout'),
    path('users/', UsersViewSet.as_view({'get': 'list', 'post': 'create'}), name='users-list-create'),
    path('image/upload/', upload_image_api, name='upload-image'),
    path('images/', list_images_api, name='list-images'),
]
