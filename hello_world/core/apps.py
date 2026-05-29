from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hello_world.core'
    verbose_name = '해솔7 커뮤니티'

    def ready(self):
        import hello_world.core.signals
