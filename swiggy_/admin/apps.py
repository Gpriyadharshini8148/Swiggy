from django.apps import AppConfig


class AdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin'
    label = 'swiggy_admin'

class AccessConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin.access'

class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin.users'

class RestaurantConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin.restaurants'

class DeliveryPartnerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin.delivery'
