from django.apps import AppConfig


class SnmpCollectorConfig(AppConfig):
    """
    Configuration de l'application SNMP Collector.

    Cette application est responsable de :
    - La collecte des métriques SNMP depuis les OLTs
    - L'historisation des données réseau (performance, état, trafic)
    - Le déclenchement des signaux liés aux événements SNMP
    - L'intégration avec les tâches Celery de polling

    Elle charge également les signaux au démarrage de l'application.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.snmp_collector'
    verbose_name = '📡 Collecteur SNMP'

    def ready(self):
        """
        Initialise les composants de l'application au démarrage Django.

        Importe les signaux afin de connecter les handlers d'événements
        (ex: alertes, mises à jour de métriques, triggers métier).
        """
        try:
            import apps.snmp_collector.signals
        except ImportError:
            pass
