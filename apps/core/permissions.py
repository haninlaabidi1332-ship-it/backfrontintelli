# apps/core/permissions.py
"""
Classes de permissions personnalisées pour IntelliOLT – AI-Powered Fiber Network Supervision Platform
"""
from rest_framework import permissions


# ========================================================================
# PERMISSIONS DE BASE
# ========================================================================

class IsAdmin(permissions.BasePermission):
    """Seuls les administrateurs peuvent accéder"""
    message = "👑 Seuls les administrateurs peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'role', None) == 'admin')


class IsSupervisor(permissions.BasePermission):
    """Superviseurs et administrateurs peuvent accéder"""
    message = "📊 Seuls les superviseurs et administrateurs peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'role', None) in ['admin', 'supervisor'])


class IsOperator(permissions.BasePermission):
    """Opérateurs, superviseurs et administrateurs peuvent accéder"""
    message = "🖥️ Seuls les opérateurs et supérieurs peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'role', None) in ['admin', 'supervisor', 'operator'])


class IsViewer(permissions.BasePermission):
    """Tout utilisateur authentifié peut accéder (lecture seule)"""
    message = "👁️ Authentification requise."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsAdminOrReadOnly(permissions.BasePermission):
    """Les administrateurs peuvent modifier, les autres lecture seule"""
    message = "✏️ Vous n'avez pas les droits de modification."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return getattr(request.user, 'role', None) == 'admin'


class IsOwnerOrAdmin(permissions.BasePermission):
    """L'utilisateur est propriétaire de l'objet ou administrateur"""
    message = "🔒 Vous n'êtes pas le propriétaire de cette ressource."
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if getattr(request.user, 'role', None) == 'admin':
            return True
        
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return False


# ========================================================================
# PERMISSIONS D'ÉTAT DU COMPTE
# ========================================================================

class IsActiveUser(permissions.BasePermission):
    """Le compte utilisateur doit être actif"""
    message = "⏸️ Votre compte n'est pas actif."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                request.user.is_active)


class HasAPIAccess(permissions.BasePermission):
    """L'utilisateur a l'accès API activé (optionnel)"""
    message = "🔑 Votre accès API est désactivé."
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                getattr(request.user, 'api_access_enabled', True))


# ========================================================================
# PERMISSIONS SPÉCIFIQUES INTELLIOLT (OLT, SNMP, BFD, ALERTES, IA, EVE-NG)
# ========================================================================

# --- OLT & Équipements réseau ---
class CanViewOLT(permissions.BasePermission):
    """Permission pour consulter les OLT"""
    message = "📡 Vous n'avez pas la permission de consulter les OLT."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', None)
        return role in ['operator', 'supervisor', 'admin']


class CanManageOLT(permissions.BasePermission):
    """Permission pour ajouter, modifier, supprimer des OLT"""
    message = "✏️ Vous n'avez pas la permission de gérer les OLT."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', None)
        return role == 'admin'


class CanViewONT(permissions.BasePermission):
    """Permission pour consulter les ONT"""
    message = "🏠 Vous n'avez pas la permission de consulter les ONT."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', None)
        return role in ['operator', 'supervisor', 'admin']


class CanManageONT(permissions.BasePermission):
    """Permission pour gérer les ONT"""
    message = "🔧 Vous n'avez pas la permission de gérer les ONT."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', None)
        return role in ['supervisor', 'admin']


# --- SNMP ---
class CanViewSNMPMetrics(permissions.BasePermission):
    """Permission pour consulter les métriques SNMP"""
    message = "📊 Vous n'avez pas la permission de consulter les métriques SNMP."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', None)
        return role in ['operator', 'supervisor', 'admin']


class CanManageSNMPOID(permissions.BasePermission):
    """Permission pour gérer les OIDs SNMP"""
    message = "⚙️ Vous n'avez pas la permission de gérer les OIDs SNMP."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', None)
        return role in ['supervisor', 'admin']


# --- BFD ---
class CanViewBFDSession(permissions.BasePermission):
    """Permission pour consulter les sessions BFD"""
    message = "🔗 Vous n'avez pas la permission de consulter les sessions BFD."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', None)
        return role in ['operator', 'supervisor', 'admin']


class CanManageBFDSession(permissions.BasePermission):
    """Permission pour gérer les sessions BFD"""
    message = "⚙️ Vous n'avez pas la permission de gérer les sessions BFD."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', None)
        return role == 'admin'


# --- Alertes ---
class CanViewAlertRule(permissions.BasePermission):
    """Permission pour consulter les règles d'alerte"""
    message = "🚨 Vous n'avez pas la permission de consulter les règles d'alerte."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', None)
        return role in ['operator', 'supervisor', 'admin']


class CanManageAlertRule(permissions.BasePermission):
    """Permission pour gérer les règles d'alerte"""
    message = "⚙️ Vous n'avez pas la permission de gérer les règles d'alerte."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', None)
        return role in ['supervisor', 'admin']


class CanViewAlert(permissions.BasePermission):
    """Permission pour consulter les alertes"""
    message = "🔔 Vous n'avez pas la permission de consulter les alertes."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class CanAcknowledgeAlert(permissions.BasePermission):
    """Permission pour acquitter les alertes"""
    message = "✅ Vous n'avez pas la permission d'acquitter les alertes."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', None)
        return role in ['operator', 'supervisor', 'admin']


class CanResolveAlert(permissions.BasePermission):
    """Permission pour résoudre les alertes"""
    message = "✔️ Vous n'avez pas la permission de résoudre les alertes."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', None)
        return role in ['operator', 'supervisor', 'admin']


# --- IA / Machine Learning ---
class CanViewAnomaly(permissions.BasePermission):
    """Permission pour consulter les anomalies détectées par IA"""
    message = "🧠 Vous n'avez pas la permission de consulter les anomalies IA."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', None)
        return role in ['operator', 'supervisor', 'admin']


class CanManageMLModel(permissions.BasePermission):
    """Permission pour gérer les modèles de ML (entraînement, activation)"""
    message = "🤖 Vous n'avez pas la permission de gérer les modèles ML."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', None)
        return role == 'admin'


# --- Tableaux de bord et exports ---
class CanViewDashboard(permissions.BasePermission):
    """Permission pour accéder aux tableaux de bord"""
    message = "📊 Vous n'avez pas la permission d'accéder aux tableaux de bord."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class CanExportData(permissions.BasePermission):
    """Permission pour exporter les données (CSV, PDF, Excel)"""
    message = "📤 Vous n'avez pas la permission d'exporter les données."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', None)
        return role in ['operator', 'supervisor', 'admin']


# --- EVE-NG (simulation réseau) ---
class CanManageLab(permissions.BasePermission):
    """Permission pour gérer les labs EVE-NG"""
    message = "🧪 Vous n'avez pas la permission de gérer les labs EVE-NG."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(request.user, 'role', None)
        return role in ['supervisor', 'admin']


# --- Clé API pour ingestion externe (ex: collecte SNMP automatisée) ---
class CanIngestData(permissions.BasePermission):
    """Permission via clé API pour ingestion de données (SNMP, scans, etc.)"""
    message = "🔑 Clé API invalide ou manquante."
    
    def has_permission(self, request, view):
        from django.conf import settings
        api_key = request.headers.get("X-API-Key")
        return api_key == getattr(settings, "INGEST_API_KEY", None)