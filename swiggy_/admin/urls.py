from django.urls import path, include, re_path
from django.views.generic import RedirectView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

schema_view = get_schema_view(
   openapi.Info(
      title="Swiggy API",
      default_version='v1',
      description="API documentation for Swiggy",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="gpriyadharshini9965@gmail.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'auth': reverse('auth-list', request=request, format=format) if 'auth-list' in request.resolver_match.view_name else '/auth/', 
        'auth': request.build_absolute_uri('auth/'),
        'users': request.build_absolute_uri('users/'),
        'restaurants': request.build_absolute_uri('restaurants/'),
        'delivery': request.build_absolute_uri('delivery/'),
    })

urlpatterns = [
    # Top-level API Root
    path('', api_root, name='api-root'),

    path('auth/', include('admin.access.urls')),
    path('users/', include('admin.users.urls')),
    path('restaurants/', include('admin.restaurants.urls')),
    path('delivery/', include('admin.delivery.urls')),

    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Legacy/Unified Paths
    path('api/auth/', include('admin.access.urls')),
    path('api/access/', include('admin.access.urls')),
    path('api/users/', include('admin.users.urls')),
    path('api/restaurants/', include('admin.restaurants.urls')),
    path('api/delivery/', include('admin.delivery.urls')),
]
