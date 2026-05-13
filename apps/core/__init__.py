"""
Application principale pour IntelliOLT – AI-Powered Fiber Network Supervision Platform.
Fournit les utilitaires de base : pagination, exceptions, middleware, helpers,
et fonctionnalités partagées pour toutes les apps métier (équipements, SNMP, BFD, alertes, IA, etc.).
"""

default_app_config = 'apps.core.apps.CoreConfig'

# Version du backend
__version__ = '1.0.0'