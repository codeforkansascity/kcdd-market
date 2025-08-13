from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    verbose_name = 'KCDD Matchmaking Portal'

    def ready(self):
        # Import any signals here if needed
        pass
