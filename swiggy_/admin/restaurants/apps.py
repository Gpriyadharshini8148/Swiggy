from django.apps import AppConfig

class RestaurantsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin.restaurants'

    def ready(self):
        import admin.restaurants.signals
