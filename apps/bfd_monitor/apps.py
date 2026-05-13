from django.apps import AppConfig

class BfdMonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.bfd_monitor'
    verbose_name = '🔗 BFD Monitor - Détection de panne rapide'

    def ready(self):
        try:
            from . import signals
        except ImportError:
            pass
        # Enregistrement de l'administration dynamique
        from .admin import register_admin
        register_admin()
        # Enregistrement des tâches périodiques (optionnel)
        from .tasks import register_beat_schedule
        register_beat_schedule()
