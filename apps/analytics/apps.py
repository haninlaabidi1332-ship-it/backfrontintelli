from django.apps import AppConfig

class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.analytics'
    verbose_name = '📈 Analytics - KPIs, rapports et dashboards'

    def ready(self):
        try:
            from . import signals
        except ImportError:
            pass
        from .admin import register_admin
        register_admin()