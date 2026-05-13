from django.apps import AppConfig

class AIEngineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai_engine'
    verbose_name = '🧠 IA Engine - Détection d\'anomalies et prédictions'

    def ready(self):
        try:
            from . import signals
        except ImportError:
            pass
        from .admin import register_admin
        register_admin()
        # Planification des tâches IA dans Celery Beat (optionnel)
        from .tasks import register_beat_schedule
        register_beat_schedule()
