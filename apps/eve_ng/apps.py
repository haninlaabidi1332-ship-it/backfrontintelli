from django.apps import AppConfig

class EveNgConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.eve_ng'
    verbose_name = '🧪 EVE-NG - Simulation réseau'

    def ready(self):
        try:
            from . import signals
        except ImportError:
            pass
        from .admin import register_admin
        register_admin()