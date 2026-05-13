from django.apps import AppConfig

class EquipementsConfig(AppConfig):
    """
    Configuration de l'application 'equipements'.
    Définit le nom, le label et le verbose_name.
    Le chargement des signaux se fait dans la méthode ready().
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.equipements'
    verbose_name = '📡 Équipements réseau (OLT, ONT)'

    def ready(self):
        # Import des signaux pour connecter les récepteurs
        try:
            import apps.equipements.signals
        except ImportError:
            pass
