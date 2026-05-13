"""
Configuration de l'application core pour IntelliOLT – AI-Powered Fiber Network Supervision Platform
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = 'apps.core'
    verbose_name = "⚙️ Core - Utilitaires de base IntelliOLT"

    def ready(self):
        # Importer les signaux (si nécessaire, par exemple pour l'initialisation)
        try:
            import apps.core.signals
        except ImportError:
            pass
