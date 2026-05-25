from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hello_world.core'  # settings.py와 일치시킵니다.
    label = 'core'
