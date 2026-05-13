# apps/core/exceptions.py
"""
Gestionnaire d'exceptions personnalisé pour IntelliOLT – AI-Powered Fiber Network Supervision Platform
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import Http404
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Gestionnaire d'exceptions personnalisé pour IntelliOLT
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "status": False,
            "message": "Une erreur est survenue.",
            "errors": {},
        }

        if hasattr(response, "data"):
            data = response.data
            if isinstance(data, dict):
                if "detail" in data:
                    error_data["message"] = str(data["detail"])
                elif "message" in data:
                    error_data["message"] = str(data["message"])
                else:
                    error_data["errors"] = data
                    error_data["message"] = "Erreur de validation."
            elif isinstance(data, list):
                error_data["errors"] = {"non_field_errors": data}
                error_data["message"] = str(data[0]) if data else "Erreur."

        status_code = response.status_code
        if status_code == 400:
            error_data["code"] = "bad_request"
        elif status_code == 401:
            error_data["code"] = "unauthorized"
            if error_data["message"] == "Une erreur est survenue.":
                error_data["message"] = "Non authentifié."
        elif status_code == 403:
            error_data["code"] = "forbidden"
            if error_data["message"] == "Une erreur est survenue.":
                error_data["message"] = "Permission refusée."
        elif status_code == 404:
            error_data["code"] = "not_found"
            if error_data["message"] == "Une erreur est survenue.":
                error_data["message"] = "Ressource non trouvée."
        elif status_code == 405:
            error_data["code"] = "method_not_allowed"
            error_data["message"] = "Méthode non autorisée."
        elif status_code == 409:
            error_data["code"] = "conflict"
            if error_data["message"] == "Une erreur est survenue.":
                error_data["message"] = "Conflit de ressource."
        elif status_code == 422:
            error_data["code"] = "validation_error"
            if error_data["message"] == "Une erreur est survenue.":
                error_data["message"] = "Erreur de validation."
        elif status_code == 429:
            error_data["code"] = "too_many_requests"
            error_data["message"] = "Trop de requêtes. Veuillez réessayer plus tard."
        elif status_code >= 500:
            error_data["code"] = "server_error"
            if error_data["message"] == "Une erreur est survenue.":
                error_data["message"] = "Erreur interne du serveur."

        response.data = error_data
        
    else:
        logger.exception("Exception non gérée: %s", exc)
        
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        message = "Erreur interne du serveur."
        code = "server_error"
        
        # Gestion des exceptions personnalisées IntelliOLT
        if isinstance(exc, IntelliOLTException):
            status_code = exc.status_code
            message = exc.message
            code = exc.code
        
        elif isinstance(exc, Http404):
            status_code = status.HTTP_404_NOT_FOUND
            message = "Ressource non trouvée."
            code = "not_found"
        
        elif isinstance(exc, PermissionDenied):
            status_code = status.HTTP_403_FORBIDDEN
            message = "Permission refusée."
            code = "forbidden"
        
        elif isinstance(exc, ValidationError):
            status_code = status.HTTP_400_BAD_REQUEST
            message = "Erreur de validation."
            code = "validation_error"
            error_data = {
                "status": False,
                "message": message,
                "errors": exc.message_dict if hasattr(exc, 'message_dict') else exc.messages,
                "code": code,
            }
            from django.utils import timezone
            error_data["timestamp"] = timezone.now().isoformat()
            return Response(error_data, status=status_code)
        
        response = Response(
            {
                "status": False,
                "message": message,
                "errors": {},
                "code": code,
            },
            status=status_code,
        )
        
        from django.utils import timezone
        response.data["timestamp"] = timezone.now().isoformat()

    return response


# ========================================================================
# EXCEPTIONS SPÉCIFIQUES INTELLIOLT
# ========================================================================

class IntelliOLTException(Exception):
    """Exception de base pour IntelliOLT - Supervision OLT avec IA"""
    
    def __init__(self, message="Une erreur IntelliOLT est survenue", code=None, status_code=400):
        self.message = message
        self.code = code or "intelliolt_error"
        self.status_code = status_code
        super().__init__(self.message)


class OLTNotFoundException(IntelliOLTException):
    """Exception pour OLT non trouvé"""
    
    def __init__(self, olt_id=None, message=None):
        if not message:
            message = f"OLT non trouvé" + (f" : {olt_id}" if olt_id else "")
        super().__init__(message, code="olt_not_found", status_code=404)


class ONTNotFoundException(IntelliOLTException):
    """Exception pour ONT non trouvé"""
    
    def __init__(self, ont_id=None, message=None):
        if not message:
            message = f"ONT non trouvé" + (f" : {ont_id}" if ont_id else "")
        super().__init__(message, code="ont_not_found", status_code=404)


class SNMPTimeoutException(IntelliOLTException):
    """Exception pour timeout SNMP"""
    
    def __init__(self, olt_hostname=None, message=None):
        if not message:
            message = f"Timeout SNMP" + (f" sur {olt_hostname}" if olt_hostname else "")
        super().__init__(message, code="snmp_timeout", status_code=504)


class SNMPConnectionException(IntelliOLTException):
    """Exception pour erreur de connexion SNMP"""
    
    def __init__(self, olt_hostname=None, reason=None, message=None):
        if not message:
            message = f"Erreur SNMP" + (f" sur {olt_hostname}" if olt_hostname else "")
            if reason:
                message += f" : {reason}"
        super().__init__(message, code="snmp_error", status_code=500)


class BFDSessionNotFoundException(IntelliOLTException):
    """Exception pour session BFD non trouvée"""
    
    def __init__(self, session_id=None, message=None):
        if not message:
            message = f"Session BFD non trouvée" + (f" : {session_id}" if session_id else "")
        super().__init__(message, code="bfd_session_not_found", status_code=404)


class InvalidAlertRuleException(IntelliOLTException):
    """Exception pour règle d'alerte invalide"""
    
    def __init__(self, rule_name=None, message=None):
        if not message:
            message = f"Règle d'alerte invalide" + (f" : {rule_name}" if rule_name else "")
        super().__init__(message, code="invalid_alert_rule", status_code=422)


class AnomalyDetectionException(IntelliOLTException):
    """Exception pour erreur de détection d'anomalie IA"""
    
    def __init__(self, detail=None, message=None):
        if not message:
            message = f"Erreur détection anomalie" + (f" : {detail}" if detail else "")
        super().__init__(message, code="anomaly_detection_error", status_code=500)


class ModelTrainingException(IntelliOLTException):
    """Exception pour échec d'entraînement du modèle ML"""
    
    def __init__(self, model_name=None, message=None):
        if not message:
            message = f"Échec entraînement modèle" + (f" : {model_name}" if model_name else "")
        super().__init__(message, code="model_training_failed", status_code=500)


class EVENotAvailableException(IntelliOLTException):
    """Exception pour indisponibilité d'EVE-NG"""
    
    def __init__(self, detail=None, message=None):
        if not message:
            message = f"EVE-NG non disponible" + (f" : {detail}" if detail else "")
        super().__init__(message, code="eve_ng_error", status_code=503)


# --- Exceptions génériques conservées (utiles) ---

class DuplicateSerialException(IntelliOLTException):
    """Exception pour numéro de série déjà existant"""
    
    def __init__(self, serial=None, message=None):
        if not message:
            message = f"Numéro de série déjà existant" + (f" : {serial}" if serial else "")
        super().__init__(message, code="duplicate_serial", status_code=409)


class ExportReportException(IntelliOLTException):
    """Exception pour échec d'export de rapport"""
    
    def __init__(self, format=None, message=None):
        if not message:
            message = f"Erreur d'export de rapport" + (f" au format {format}" if format else "")
        super().__init__(message, code="export_error", status_code=500)


class NotificationException(IntelliOLTException):
    """Exception pour échec d'envoi de notification"""
    
    def __init__(self, channel=None, reason=None, message=None):
        if not message:
            message = f"Erreur de notification" + (f" sur {channel}" if channel else "")
            if reason:
                message += f" : {reason}"
        super().__init__(message, code="notification_error", status_code=500)


class PermissionDeniedException(IntelliOLTException):
    """Exception pour permission refusée"""
    
    def __init__(self, required_permission=None, message=None):
        if not message:
            message = "Permission refusée"
            if required_permission:
                message += f" : {required_permission} requis"
        super().__init__(message, code="permission_denied", status_code=403)