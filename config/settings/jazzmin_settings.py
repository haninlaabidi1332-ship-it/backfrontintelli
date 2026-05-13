# config/settings/jazzmin_settings.py
"""
Paramètres Jazzmin pour IntelliOLT – AI-Powered Fiber Network Supervision Platform
Apps : Core, Users, Equipements, SNMP Collector, BFD Monitor, Alerting, AI Engine, Analytics, EVE-NG
"""

# ------------------------------
# 1. CONFIGURATION PRINCIPALE JAZZMIN
# ------------------------------
JAZZMIN_SETTINGS = {
    # MARQUE / IDENTITÉ
    "site_title": "IntelliOLT Admin",
    "site_header": "IntelliOLT",
    "site_brand": "🤖 IntelliOLT",
    "site_logo": None,
    "login_logo": None,
    "site_icon": None,
    "welcome_sign": "🌟 Bienvenue sur IntelliOLT - Supervision intelligente des OLT",
    "copyright": "IntelliOLT | v1.0.0",

    # LIENS DU MENU SUPÉRIEUR
    "topmenu_links": [
        {"name": "🏠 Tableau de bord", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "⚙️ Core", "url": "/admin/core/", "new_window": False},
        {"name": "👥 Utilisateurs", "url": "/admin/users/", "new_window": False},
        {"name": "📡 Équipements (OLT/ONT)", "url": "/admin/equipements/", "new_window": False},
        {"name": "📊 SNMP", "url": "/admin/snmp_collector/", "new_window": False},
        {"name": "🔗 BFD", "url": "/admin/bfd_monitor/", "new_window": False},
        {"name": "🚨 Alertes", "url": "/admin/alerting/", "new_window": False},
        {"name": "🧠 IA / Anomalies", "url": "/admin/ai_engine/", "new_window": False},
        {"name": "📈 Analytics", "url": "/admin/analytics/", "new_window": False},
        {"name": "🧪 EVE-NG", "url": "/admin/eve_ng/", "new_window": False},
        {"name": "📚 Doc API", "url": "/api/schema/swagger-ui/", "new_window": True},
        {"name": "📖 ReDoc", "url": "/api/schema/redoc/", "new_window": True},
        {"name": "📧 Support", "url": "mailto:support@intelliolt.com", "new_window": True},
    ],

    # LIENS DU MENU UTILISATEUR
    "usermenu_links": [
        {"model": "users.user"},
        {"name": "🔐 Mon profil", "url": "/admin/users/user/", "icon": "fas fa-user-circle"},
        {"name": "⚙️ Paramètres compte", "url": "/admin/account/", "icon": "fas fa-cog"},
        {"name": "📄 Documentation", "url": "https://docs.intelliolt.com", "new_window": True},
    ],

    "show_sidebar": True,
    "navigation_expanded": False,
    "hide_apps": [],
    "hide_models": [],

    # ORDRE D'AFFICHAGE DANS LA BARRE LATÉRALE
    "order_with_respect_to": [
        "users",
        "core",
        "equipements",
        "snmp_collector",
        "bfd_monitor",
        "alerting",
        "ai_engine",
        "analytics",
        "eve_ng",
        "auth",
        "authtoken",
        "token_blacklist",
        "django_celery_beat",
        "django_celery_results",
    ],

    # ICÔNES PAR APPLICATION / MODÈLE (liste exhaustive)
    "icons": {
        # Utilisateurs
        "users": "fas fa-users-cog",
        "users.User": "fas fa-user-circle",
        "users.Team": "fas fa-users",
        "users.Role": "fas fa-user-tag",
        "users.Permission": "fas fa-key",
        "users.UserActivity": "fas fa-history",

        # Core
        "core": "fas fa-cogs",
        "core.Config": "fas fa-sliders-h",

        # Équipements
        "equipements": "fas fa-server",
        "equipements.OLT": "fas fa-network-wired",
        "equipements.ONT": "fas fa-wifi",
        "equipements.Vendor": "fas fa-building",
        "equipements.FibreLink": "fas fa-link",
        "equipements.Site": "fas fa-map-marker-alt",
        "equipements.GponPort": "fas fa-plug",
        "equipements.Splitter": "fas fa-code-branch",

        # SNMP
        "snmp_collector": "fas fa-chart-line",
        "snmp_collector.SnmpOID": "fas fa-tag",
        "snmp_collector.MetricHistory": "fas fa-database",
        "snmp_collector.PollJob": "fas fa-tasks",
        "snmp_collector.SnmpThresholdRule": "fas fa-sliders-h",
        "snmp_collector.SnmpAlert": "fas fa-exclamation-triangle",

        # BFD
        "bfd_monitor": "fas fa-shield-alt",
        "bfd_monitor.BFDSession": "fas fa-exchange-alt",
        "bfd_monitor.BFDStateHistory": "fas fa-history",
        "bfd_monitor.BFDThresholdRule": "fas fa-sliders-h",
        "bfd_monitor.BFDActiveAlert": "fas fa-bell",

        # Alerting
        "alerting": "fas fa-bell",
        "alerting.AlertRule": "fas fa-sliders-h",
        "alerting.Alert": "fas fa-exclamation-triangle",
        "alerting.NotificationChannel": "fas fa-envelope",

        # AI Engine
        "ai_engine": "fas fa-brain",
        "ai_engine.MLModel": "fas fa-microchip",
        "ai_engine.AnomalyDetection": "fas fa-chart-line",
        "ai_engine.Prediction": "fas fa-chart-simple",
        "ai_engine.TrainingJob": "fas fa-cogs",

        # Analytics
        "analytics": "fas fa-chart-bar",
        "analytics.KPIHistory": "fas fa-chart-simple",
        "analytics.Report": "fas fa-file-alt",
        "analytics.DashboardWidget": "fas fa-tachometer-alt",

        # EVE-NG
        "eve_ng": "fas fa-microchip",
        "eve_ng.EveNgLab": "fas fa-flask",
        "eve_ng.EveNgDevice": "fas fa-server",
        "eve_ng.EveNgLabExecution": "fas fa-play",

        # Authentification tierce
        "auth": "fas fa-lock",
        "auth.Group": "fas fa-users-cog",
        "auth.Permission": "fas fa-key",
        "authtoken": "fas fa-key",
        "authtoken.Token": "fas fa-token",
        "token_blacklist": "fas fa-ban",
        "django_celery_beat": "fas fa-clock",
        "django_celery_results": "fas fa-chart-line",
    },

    "default_icon_parents": "fas fa-folder-open",
    "default_icon_children": "fas fa-file",

    # LIENS RAPIDES PAR APPLICATION (custom_links)
    "custom_links": {
        "users": [
            {"name": "➕ Ajouter utilisateur", "url": "/admin/users/user/add/", "icon": "fas fa-user-plus", "permissions": ["users.add_user"]},
            {"name": "👥 Nouvelle équipe", "url": "/admin/users/team/add/", "icon": "fas fa-users", "permissions": ["users.add_team"]},
            {"name": "🎭 Nouveau rôle", "url": "/admin/users/role/add/", "icon": "fas fa-user-tag", "permissions": ["users.add_role"]},
            {"name": "🔑 Nouvelle permission", "url": "/admin/users/permission/add/", "icon": "fas fa-key", "permissions": ["users.add_permission"]},
            {"name": "📊 Voir activités", "url": "/admin/users/useractivity/", "icon": "fas fa-history", "permissions": ["users.view_useractivity"]},
        ],
        "core": [
            {"name": "⚙️ Nouvelle config", "url": "/admin/core/config/add/", "icon": "fas fa-plus-circle", "permissions": ["core.add_config"]},
            {"name": "📋 Liste configs", "url": "/admin/core/config/", "icon": "fas fa-list", "permissions": ["core.view_config"]},
        ],
        "equipements": [
            {"name": "➕ Nouvel OLT", "url": "/admin/equipements/olt/add/", "icon": "fas fa-plus", "permissions": ["equipements.add_olt"]},
            {"name": "📡 Nouvel ONT", "url": "/admin/equipements/ont/add/", "icon": "fas fa-wifi", "permissions": ["equipements.add_ont"]},
            {"name": "🔗 Nouvelle fibre", "url": "/admin/equipements/fibrelink/add/", "icon": "fas fa-link", "permissions": ["equipements.add_fibrelink"]},
            {"name": "🏢 Nouveau site", "url": "/admin/equipements/site/add/", "icon": "fas fa-map-marker-alt", "permissions": ["equipements.add_site"]},
        ],
        "snmp_collector": [
            {"name": "➕ Nouvel OID", "url": "/admin/snmp_collector/snmpoid/add/", "icon": "fas fa-tag", "permissions": ["snmp_collector.add_snmpoid"]},
            {"name": "📊 Voir métriques", "url": "/admin/snmp_collector/metrichistory/", "icon": "fas fa-chart-line", "permissions": ["snmp_collector.view_metrichistory"]},
            {"name": "📋 Jobs de collecte", "url": "/admin/snmp_collector/polljob/", "icon": "fas fa-tasks", "permissions": ["snmp_collector.view_polljob"]},
        ],
        "bfd_monitor": [
            {"name": "🔗 Nouvelle session BFD", "url": "/admin/bfd_monitor/bfdsession/add/", "icon": "fas fa-exchange-alt", "permissions": ["bfd_monitor.add_bfdsession"]},
            {"name": "📜 Historique", "url": "/admin/bfd_monitor/bfdstatehistory/", "icon": "fas fa-history", "permissions": ["bfd_monitor.view_bfdstatehistory"]},
            {"name": "⚙️ Règles de seuil", "url": "/admin/bfd_monitor/bfdthresholdrule/", "icon": "fas fa-sliders-h", "permissions": ["bfd_monitor.view_bfdthresholdrule"]},
        ],
        "alerting": [
            {"name": "⚙️ Nouvelle règle", "url": "/admin/alerting/alertrule/add/", "icon": "fas fa-sliders-h", "permissions": ["alerting.add_alertrule"]},
            {"name": "🚨 Voir alertes", "url": "/admin/alerting/alert/", "icon": "fas fa-bell", "permissions": ["alerting.view_alert"]},
            {"name": "📧 Canaux de notif.", "url": "/admin/alerting/notificationchannel/", "icon": "fas fa-envelope", "permissions": ["alerting.view_notificationchannel"]},
        ],
        "ai_engine": [
            {"name": "🧠 Nouveau modèle", "url": "/admin/ai_engine/mlmodel/add/", "icon": "fas fa-microchip", "permissions": ["ai_engine.add_mlmodel"]},
            {"name": "⚠️ Anomalies", "url": "/admin/ai_engine/anomalydetection/", "icon": "fas fa-chart-line", "permissions": ["ai_engine.view_anomalydetection"]},
            {"name": "📈 Prédictions", "url": "/admin/ai_engine/prediction/", "icon": "fas fa-chart-simple", "permissions": ["ai_engine.view_prediction"]},
        ],
        "analytics": [
            {"name": "📈 Voir KPIs", "url": "/admin/analytics/kpihistory/", "icon": "fas fa-chart-simple", "permissions": ["analytics.view_kpihistory"]},
            {"name": "📄 Générer rapport", "url": "/admin/analytics/report/add/", "icon": "fas fa-file-alt", "permissions": ["analytics.add_report"]},
        ],
        "eve_ng": [
            {"name": "🧪 Nouveau lab", "url": "/admin/eve_ng/eve_nglab/add/", "icon": "fas fa-flask", "permissions": ["eve_ng.add_evenglab"]},
            {"name": "💻 Périphériques", "url": "/admin/eve_ng/evengdevice/", "icon": "fas fa-server", "permissions": ["eve_ng.view_evengdevice"]},
        ],
    },

    "related_modal_active": True,
    "custom_css": None,
    "custom_js": None,
    "show_ui_builder": False,

    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "users.user": "vertical_tabs",
        "users.team": "horizontal_tabs",
        "users.role": "collapsible",
        "core.config": "horizontal_tabs",
        "equipements.olt": "vertical_tabs",
        "equipements.ont": "horizontal_tabs",
        "snmp_collector.metrichistory": "horizontal_tabs",
        "bfd_monitor.bfdsession": "vertical_tabs",
        "alerting.alertrule": "vertical_tabs",
        "alerting.alert": "vertical_tabs",
        "ai_engine.mlmodel": "vertical_tabs",
        "ai_engine.anomalydetection": "horizontal_tabs",
    },

    "language_chooser": False,
}


# ------------------------------
# 2. PERSONNALISATION UI TWEAKS
# ------------------------------
JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "dark_mode_theme": "darkly",
    "navbar_small_text": False,
    "navbar_fixed": True,
    "navbar": "navbar-light bg-white",
    "navbar_class": "shadow-sm border-bottom",
    "sidebar": "sidebar-light-primary",
    "sidebar_fixed": True,
    "sidebar_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "footer_fixed": False,
    "footer_small_text": True,
    "brand_small_text": False,
    "brand_colour": "navbar-light",
    "brand_colour_bg": "bg-white",
    "body_small_text": False,
    "no_navbar_border": False,
    "layout_boxed": False,
    "accent": "accent-primary",
    "button_classes": {
        "primary": "btn-primary btn-sm",
        "secondary": "btn-secondary btn-sm",
        "info": "btn-info btn-sm",
        "warning": "btn-warning btn-sm",
        "danger": "btn-danger btn-sm",
        "success": "btn-success btn-sm",
        "outline-primary": "btn-outline-primary btn-sm",
    },
    "actions_sticky_top": True,
}


# ------------------------------
# 3. TABLEAU DE BORD PERSONNALISÉ (JAZZMIN_DASHBOARD)
# ------------------------------
def _get_dashboard_stats():
    """
    Fonction utilitaire pour récupérer les statistiques dynamiques du dashboard.
    Utilisée par JAZZMIN_DASHBOARD via formatage de chaîne.
    """
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Count

    User = get_user_model()
    stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'total_olts': 0,
        'bfd_up_count': 0,
        'active_alerts': 0,
        'anomalies_24h': 0,
    }

    try:
        from apps.equipements.models import OLT
        stats['total_olts'] = OLT.objects.filter(status='active').count()
    except (ImportError, Exception):
        pass

    try:
        from apps.bfd_monitor.models import BFDSession
        stats['bfd_up_count'] = BFDSession.objects.filter(state='up').count()
    except (ImportError, Exception):
        pass

    try:
        from apps.alerting.models import Alert
        stats['active_alerts'] = Alert.objects.filter(status='active').count()
    except (ImportError, Exception):
        pass

    try:
        from apps.ai_engine.models import AnomalyDetection
        last_24h = timezone.now() - timedelta(hours=24)
        stats['anomalies_24h'] = AnomalyDetection.objects.filter(detected_at__gte=last_24h).count()
    except (ImportError, Exception):
        pass

    return stats


# On construit le dictionnaire du dashboard avec des chaînes formatables
JAZZMIN_DASHBOARD = {
    "welcome_message": """
        <div class="alert alert-primary alert-dismissible fade show" role="alert">
            <strong>👋 Bienvenue {user} !</strong>
            <span class="badge bg-success ms-2">{active_users}/{total_users} utilisateurs actifs</span>
            <span class="badge bg-info ms-2">{total_olts} OLT</span>
            <span class="badge bg-warning ms-2">{active_alerts} alertes actives</span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    """,

    "quick_actions": [
        {"name": "➕ Ajouter utilisateur", "url": "/admin/users/user/add/", "icon": "fas fa-user-plus", "color": "success"},
        {"name": "📡 Ajouter OLT", "url": "/admin/equipements/olt/add/", "icon": "fas fa-server", "color": "primary"},
        {"name": "📊 Ajouter OID SNMP", "url": "/admin/snmp_collector/snmpoid/add/", "icon": "fas fa-chart-line", "color": "info"},
        {"name": "🔄 Ajouter session BFD", "url": "/admin/bfd_monitor/bfdsession/add/", "icon": "fas fa-exchange-alt", "color": "secondary"},
        {"name": "⚙️ Nouvelle règle d'alerte", "url": "/admin/alerting/alertrule/add/", "icon": "fas fa-sliders-h", "color": "warning"},
        {"name": "🧠 Entraîner un modèle IA", "url": "/admin/ai_engine/mlmodel/add/", "icon": "fas fa-brain", "color": "dark"},
    ],

    "stats_cards": [
        {"title": "Total OLT", "value": "{total_olts}", "icon": "fas fa-server", "color": "primary"},
        {"title": "Sessions BFD UP", "value": "{bfd_up_count}", "icon": "fas fa-shield-alt", "color": "success"},
        {"title": "Alertes actives", "value": "{active_alerts}", "icon": "fas fa-bell", "color": "danger"},
        {"title": "Anomalies (24h)", "value": "{anomalies_24h}", "icon": "fas fa-brain", "color": "warning"},
    ],

    "recent_activities": {
        "title": "🕒 Activités récentes",
        "limit": 10,
        "model": "users.UserActivity",
        "fields": ["user", "action", "description", "created_at"],
        "order_by": ["-created_at"],
    },

    "recent_alerts": {
        "title": "🚨 Alertes récentes",
        "limit": 5,
        "model": "alerting.Alert",
        "fields": ["severity", "message", "status", "first_seen"],
        "order_by": ["-first_seen"],
    },

    "recent_anomalies": {
        "title": "⚠️ Anomalies détectées",
        "limit": 5,
        "model": "ai_engine.AnomalyDetection",
        "fields": ["olt", "metric_name", "actual_value", "anomaly_score", "detected_at"],
        "order_by": ["-detected_at"],
    },
}

# Optionnel : Pour injecter les statistiques réelles dans le dashboard, on peut surcharger
# la méthode get_context_data de l’admin. Cela se fait généralement dans admin.py du projet principal.
# Ici on laisse les placeholders string.format, et l’affichage final sera assuré par le template jazzmin.