from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthViewSet

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = [
    path('login/', AuthViewSet.as_view({'post': 'login'}), name='login'),
    path('', include(router.urls)),
]
