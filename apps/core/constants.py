# apps/core/constants.py
"""
Constantes globales pour IntelliOLT – AI-Powered Fiber Network Supervision Platform
"""

# Méthodes HTTP
HTTP_METHODS = {
    'GET': 'GET',
    'POST': 'POST',
    'PUT': 'PUT',
    'PATCH': 'PATCH',
    'DELETE': 'DELETE',
    'OPTIONS': 'OPTIONS',
    'HEAD': 'HEAD',
}

# Méthodes sûres (lecture seule)
SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']

# Informations de la plateforme
PLATFORM = {
    'name': 'IntelliOLT - Supervision OLT avec IA',
    'version': '1.0.0',
    'description': 'Plateforme intelligente de supervision d\'équipements OLT avec SNMP, BFD et Machine Learning',
    'website': 'https://intelliolt.com',
    'company': 'IntelliOLT',
    'support_email': 'support@intelliolt.com',
}

# Pagination par défaut
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Durées de cache (secondes)
CACHE_TTL = {
    'short': 60,           # 1 minute
    'medium': 300,         # 5 minutes
    'long': 3600,          # 1 heure
    'day': 86400,          # 1 jour
    'week': 604800,        # 1 semaine
    'month': 2592000,      # 30 jours
}

# ============================================================================
# CONSTANTES RÉSEAU & ÉQUIPEMENTS (OLT, ONT, liens)
# ============================================================================

# Types d'équipements réseau
EQUIPMENT_TYPES = {
    'olt': '🏢 OLT (Optical Line Terminal)',
    'ont': '🏠 ONT (Optical Network Terminal)',
    'router': '🌐 Routeur',
    'switch': '🔌 Switch',
    'link': '🔗 Lien fibre',
}

# Statuts des équipements
EQUIPMENT_STATUS = {
    'operational': '✅ Opérationnel',
    'maintenance': '🔧 En maintenance',
    'fault': '❌ Défaillant',
    'decommissioned': '🗑️ Hors service',
    'planned': '📅 Planifié',
    'unknown': '❓ Inconnu',
}

# Fabricants d'OLT
OLT_VENDORS = {
    'huawei': 'Huawei',
    'zte': 'ZTE',
    'nokia': 'Nokia',
    'cisco': 'Cisco',
    'alcatel': 'Alcatel-Lucent',
    'other': 'Autre',
}

# ============================================================================
# CONSTANTES SNMP
# ============================================================================

# Versions SNMP supportées
SNMP_VERSIONS = {
    '1': 'SNMPv1',
    '2c': 'SNMPv2c',
    '3': 'SNMPv3',
}

# Intervalles de polling par défaut (secondes)
SNMP_POLLING_INTERVALS = {
    'default': 60,
    'critical': 30,
    'low': 300,
}

# OIDs SNMP courants pour OLT (exemples)
SNMP_OIDS = {
    'sysUpTime': '1.3.6.1.2.1.1.3.0',
    'sysName': '1.3.6.1.2.1.1.5.0',
    'cpu_usage': '1.3.6.1.4.1.2011.6.3.4.1.2.0',  # Huawei
    'memory_usage': '1.3.6.1.4.1.2011.6.3.4.1.3.0',
    'temperature': '1.3.6.1.4.1.2011.6.3.4.1.4.0',
    'rx_power': '1.3.6.1.4.1.2011.6.3.4.1.5.0',
    'tx_power': '1.3.6.1.4.1.2011.6.3.4.1.6.0',
}

# ============================================================================
# CONSTANTES BFD (Bidirectional Forwarding Detection)
# ============================================================================

# États des sessions BFD
BFD_STATES = {
    'admin_down': 'Admin Down',
    'down': 'Down',
    'init': 'Init',
    'up': 'Up',
}

# Intervalles par défaut (ms)
BFD_DEFAULT_INTERVALS = {
    'tx': 100,
    'rx': 100,
    'multiplier': 3,
    'detect_time': 300,
}

# ============================================================================
# CONSTANTES ALERTES & NOTIFICATIONS
# ============================================================================

# Niveaux de sévérité des alertes
ALERT_SEVERITIES = {
    'info': 'ℹ️ Information',
    'warning': '⚠️ Avertissement',
    'major': '🟠 Majeure',
    'critical': '🔴 Critique',
}

# Types d'alertes
ALERT_TYPES = {
    'olt_down': '📡 OLT hors ligne',
    'ont_down': '🏠 ONT hors ligne',
    'high_cpu': '📈 CPU élevé',
    'high_memory': '💾 Mémoire élevée',
    'high_temperature': '🌡️ Température élevée',
    'rx_power_low': '📉 Puissance RX faible',
    'tx_power_high': '📈 Puissance TX élevée',
    'bfd_down': '🔗 Session BFD Down',
    'link_flapping': '🔄 Flapping de lien',
    'anomaly_detected': '🧠 Anomalie IA détectée',
}

# Statuts des alertes
ALERT_STATUS = {
    'active': '🔴 Active',
    'acknowledged': '✅ Acquittée',
    'resolved': '✔️ Résolue',
    'ignored': '🚫 Ignorée',
}

# Canaux de notification
NOTIFICATION_CHANNELS = {
    'email': 'Email',
    'sms': 'SMS',
    'webhook': 'Webhook',
    'slack': 'Slack',
    'teams': 'Microsoft Teams',
}

# ============================================================================
# CONSTANTES IA / MACHINE LEARNING
# ============================================================================

# Types de modèles ML
ML_MODEL_TYPES = {
    'random_forest': 'Random Forest',
    'isolation_forest': 'Isolation Forest',
    'lstm': 'LSTM (réseau neuronal)',
    'prophet': 'Prophet (prédiction)',
}

# Seuils pour les anomalies
ANOMALY_THRESHOLDS = {
    'default_score': 0.5,
    'high_score': 0.8,
    'low_score': 0.2,
}

# ============================================================================
# CONSTANTES ANALYTICS & DASHBOARDS
# ============================================================================

# Périodes par défaut pour les graphiques
DEFAULT_PERIODS = {
    'hour': 'Dernière heure',
    'day': 'Dernières 24h',
    'week': '7 derniers jours',
    'month': '30 derniers jours',
}

# Métriques affichables
METRICS = {
    'cpu': 'CPU (%)',
    'memory': 'Mémoire (%)',
    'temperature': 'Température (°C)',
    'rx_power': 'Puissance RX (dBm)',
    'tx_power': 'Puissance TX (dBm)',
    'uptime': 'Uptime (secondes)',
    'link_utilization': 'Utilisation lien (%)',
}

# ============================================================================
# CONSTANTES UTILISATEURS & RÔLES
# ============================================================================

USER_ROLES = {
    'admin': '👑 Administrateur',
    'supervisor': '📊 Superviseur NOC',
    'operator': '🖥️ Opérateur',
    'viewer': '👁️ Observateur',
}

# ============================================================================
# CONSTANTES EVE-NG (simulation réseau)
# ============================================================================

EVE_NG_DEFAULT_SETTINGS = {
    'api_version': '2.0',
    'lab_status': ['stopped', 'running', 'saved'],
}

# ============================================================================
# MESSAGES D'ERREUR
# ============================================================================

ERROR_MESSAGES = {
    'olt_not_found': 'OLT non trouvé',
    'ont_not_found': 'ONT non trouvé',
    'snmp_timeout': 'Timeout SNMP - équipement injoignable',
    'snmp_error': 'Erreur SNMP',
    'bfd_session_not_found': 'Session BFD non trouvée',
    'invalid_alert_rule': 'Règle d\'alerte invalide',
    'permission_denied': 'Permission refusée',
    'invalid_data': 'Données invalides',
    'database_error': 'Erreur base de données',
    'export_failed': 'Échec de l\'export',
    'model_training_failed': 'Entraînement du modèle ML échoué',
    'eve_ng_connection_error': 'Erreur de connexion à EVE-NG',
}