# apps/users/apps.py
"""
Configuration de l'application utilisateurs pour IntelliOLT – AI-Powered Fiber Network Supervision Platform
"""
from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = '👥 Utilisateurs - Gestion des utilisateurs IntelliOLT'

    def ready(self):
        # Importer les signaux
        try:
            import apps.users.signals
        except ImportError:
            pass
