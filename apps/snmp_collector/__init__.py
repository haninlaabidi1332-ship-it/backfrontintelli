"""
SNMP Collector App
===================

Cette application gère la collecte SNMP des équipements réseau (OLT, ONT, interfaces),
le stockage des métriques et le suivi des jobs de polling.

Fonctionnalités principales :
- Catalogue des OIDs SNMP
- Collecte périodique via Celery
- Historisation des métriques
- Suivi des jobs de polling
- Support multi-vendor
"""

default_app_config = "apps.snmp_collector.apps.SnmpCollectorConfig"

__version__ = "1.0.0"