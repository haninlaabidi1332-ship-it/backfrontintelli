from django.apps import AppConfig

class AlertingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.alerting'
    verbose_name = '🚨 Alerting - Règles, alertes et notifications'

    def ready(self):
        try:
            from . import signals
        except ImportError:
            pass
        from .admin import register_admin
        register_admin()
