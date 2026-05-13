# apps/core/validators.py
"""
Validateurs complets pour IntelliOLT – AI-Powered Fiber Network Supervision Platform
- Validation des OLT, ONT, équipements réseau
- Validation des seuils d'alerte (CPU, mémoire, température, SNR)
- Sécurité SQL et paramètres
- Validation des planifications CRON
- Validation des fichiers et formats
- Validation SNMP / BFD
"""
import re
import json
import sqlparse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


# ============================================================================
# CRON ET PLANIFICATION (pour tâches automatisées)
# ============================================================================

def validate_cron_expression(value):
    """
    Valide une expression CRON pour les tâches planifiées (collecte SNMP, alertes, rapports)
    Supporte les formats 5 et 6 champs
    """
    if not value:
        return value
    
    parts = value.strip().split()
    if len(parts) not in [5, 6]:
        raise ValidationError(
            _("Format CRON invalide. Utilisez 5 ou 6 champs: minute hour day month weekday [year]"),
            code='invalid_cron_parts'
        )
    
    minute, hour, day, month, weekday = parts[:5]
    
    # Patterns pour chaque champ
    pattern = r'^(\*|\d+|\d+-\d+|\d+(,\d+)*)(/\d+)?$'
    
    if not re.match(pattern, minute):
        raise ValidationError(_(f"Champ minute invalide: {minute}"), code='invalid_cron_minute')
    if not re.match(pattern, hour):
        raise ValidationError(_(f"Champ heure invalide: {hour}"), code='invalid_cron_hour')
    if not re.match(pattern, day):
        raise ValidationError(_(f"Champ jour invalide: {day}"), code='invalid_cron_day')
    if not re.match(pattern, month):
        raise ValidationError(_(f"Champ mois invalide: {month}"), code='invalid_cron_month')
    if not re.match(pattern, weekday):
        raise ValidationError(_(f"Champ jour semaine invalide: {weekday}"), code='invalid_cron_weekday')
    
    return value


def validate_schedule_interval(value):
    """
    Valide un intervalle de planification pour les tâches récurrentes (polling SNMP, vérification BFD)
    """
    if not value:
        return value
    
    valid_intervals = ['minute', 'hour', 'day', 'week', 'month']
    
    if value not in valid_intervals:
        raise ValidationError(
            _(f"Intervalle invalide. Choisir parmi: {', '.join(valid_intervals)}"),
            code='invalid_interval'
        )
    
    return value


# ============================================================================
# JSON ET YAML (pour configurations)
# ============================================================================

def validate_json_schema(value):
    """
    Valide un schéma JSON (pour les configurations système, règles d'alerte, etc.)
    """
    if not value:
        return value
    
    try:
        if isinstance(value, str):
            json.loads(value)
        elif isinstance(value, (dict, list)):
            json.dumps(value)
        else:
            raise ValueError
    except (ValueError, TypeError, json.JSONDecodeError):
        raise ValidationError(
            _("La valeur doit être un JSON valide"),
            code='invalid_json'
        )
    
    return value


def validate_yaml_content(value):
    """
    Valide le contenu YAML (pour les configurations avancées, templates EVE-NG)
    """
    if not value or not value.strip():
        raise ValidationError(_("Le contenu ne peut pas être vide"), code='empty_yaml')
    
    try:
        import yaml
        parsed = yaml.safe_load(value)
        if parsed is None:
            raise ValidationError(_("Le contenu YAML est vide"), code='empty_parsed_yaml')
        return value
    except ImportError:
        # yaml non installé, validation basique
        if '---' in value or '...' in value:
            return value
        raise ValidationError(_("Contenu YAML invalide"), code='invalid_yaml')
    except Exception as e:
        raise ValidationError(_(f"Erreur de syntaxe YAML: {str(e)}"), code='yaml_error')


# ============================================================================
# SQL ET REQUÊTES (SÉCURITÉ pour rapports personnalisés)
# ============================================================================

def validate_sql_query(value):
    """
    Valide une requête SQL avec vérification de sécurité (lecture seule)
    """
    if not value:
        return value
    
    value = value.strip()
    
    try:
        parsed = sqlparse.parse(value)
        if not parsed:
            raise ValidationError(_("Requête SQL vide"), code='empty_query')
        
        query_upper = value.upper()
        
        # Mots-clés dangereux
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 
            'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE', 'SP_', 'XP_'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise ValidationError(
                    _(f"La requête contient le mot-clé interdit: {keyword}"),
                    code='dangerous_query'
                )
        
        # Vérifier les requêtes multiples
        statements = [s for s in value.split(';') if s.strip()]
        if len(statements) > 1:
            raise ValidationError(
                _("Les requêtes multiples ne sont pas autorisées"),
                code='multiple_statements'
            )
        
        # Vérifier que c'est une requête SELECT
        first_statement = sqlparse.parse(statements[0])[0]
        first_token = next((t for t in first_statement.tokens if t.ttype is sqlparse.tokens.Keyword.DML), None)
        
        if not first_token or first_token.value.upper() != 'SELECT':
            raise ValidationError(
                _("Seules les requêtes SELECT sont autorisées"),
                code='not_select_query'
            )
            
    except Exception as e:
        raise ValidationError(
            _(f"Erreur de syntaxe SQL: {str(e)}"),
            code='invalid_sql'
        )
    
    return value


def validate_query_parameters(params):
    """
    Valide les paramètres de requête (contre les injections)
    """
    if not params:
        return params
    
    if not isinstance(params, dict):
        raise ValidationError(_("Les paramètres doivent être un dictionnaire"), code='invalid_params')
    
    for key, value in params.items():
        if not isinstance(key, str):
            raise ValidationError(_(f"La clé du paramètre doit être une chaîne: {key}"), code='invalid_param_key')
        
        if isinstance(value, str):
            dangerous = ['--', ';', 'DROP', 'DELETE', 'INSERT', 'UPDATE']
            value_upper = value.upper()
            for pattern in dangerous:
                if pattern in value_upper:
                    raise ValidationError(
                        _(f"Le paramètre '{key}' contient un motif dangereux: {pattern}"),
                        code='dangerous_param'
                    )
    
    return params


def validate_sql_identifier(value):
    """
    Valide un identifiant SQL (nom de table, colonne, etc.)
    """
    if not value:
        return value
    
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    if not re.match(pattern, value):
        raise ValidationError(
            _("Identifiant SQL invalide. Utilisez lettres, chiffres et underscore"),
            code='invalid_sql_identifier'
        )
    
    # Mots réservés SQL
    reserved_words = {
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER',
        'TABLE', 'VIEW', 'INDEX', 'DATABASE', 'SCHEMA', 'WHERE', 'FROM', 'JOIN',
        'GROUP', 'ORDER', 'BY', 'HAVING', 'LIMIT', 'OFFSET', 'UNION', 'INTERSECT',
        'EXCEPT', 'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'AND', 'OR',
        'NOT', 'IN', 'LIKE', 'BETWEEN', 'IS', 'NULL', 'TRUE', 'FALSE', 'AS'
    }
    
    if value.upper() in reserved_words:
        raise ValidationError(
            _(f"L'identifiant '{value}' est un mot réservé SQL"),
            code='reserved_word'
        )
    
    return value


# ============================================================================
# SOURCES DE DONNÉES (connexions aux bases externes, optionnel)
# ============================================================================

def validate_connection_string(value):
    """
    Valide une chaîne de connexion à une base de données (PostgreSQL, MySQL)
    """
    if not value:
        return value
    
    patterns = {
        'postgresql': r'^postgresql://([^:]+):([^@]+)@([^:/]+):?(\d+)?/([^?]+)',
        'mysql': r'^mysql://([^:]+):([^@]+)@([^:/]+):?(\d+)?/([^?]+)',
    }
    
    valid = False
    for name, pattern in patterns.items():
        if re.match(pattern, value):
            valid = True
            break
    
    if not valid:
        raise ValidationError(
            _("Format de connexion invalide. Utilisez: protocol://user:pass@host:port/database"),
            code='invalid_connection_string'
        )
    
    return value


def validate_hostname(value):
    """
    Valide un nom d'hôte ou une adresse IP (pour les OLT, serveurs SNMP)
    """
    if not value:
        return value
    
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
    hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    
    if not (re.match(ipv4_pattern, value) or re.match(ipv6_pattern, value) or re.match(hostname_pattern, value)):
        raise ValidationError(_("Nom d'hôte ou adresse IP invalide"), code='invalid_hostname')
    
    return value


def validate_port(value):
    """
    Valide un numéro de port (1-65535) pour SNMP, BFD, etc.
    """
    if value is None:
        return value
    
    try:
        port = int(value)
        if not (1 <= port <= 65535):
            raise ValueError
        return port
    except (ValueError, TypeError):
        raise ValidationError(_("Le port doit être un nombre entre 1 et 65535"), code='invalid_port')


# ============================================================================
# VALIDATEURS POUR ÉQUIPEMENTS RÉSEAU (OLT, ONT)
# ============================================================================

def validate_equipment_serial(value):
    """
    Valide un numéro de série d'équipement (alphanumérique, traits, espaces autorisés)
    """
    if not value:
        return value
    
    if not re.match(r'^[a-zA-Z0-9\-_\.\s]+$', value):
        raise ValidationError(
            _("Numéro de série invalide (caractères autorisés: alphanumériques, -, _, ., espace)"),
            code='invalid_serial'
        )
    return value


def validate_snmp_community(value):
    """
    Valide une chaîne de communauté SNMP (ne doit pas contenir d'espace)
    """
    if not value:
        return value
    
    if re.search(r'\s', value):
        raise ValidationError(
            _("La communauté SNMP ne doit pas contenir d'espace"),
            code='invalid_snmp_community'
        )
    return value


def validate_bfd_interval(value):
    """
    Valide un intervalle BFD (ms) – entre 50 et 10000 ms
    """
    if value is None:
        return value
    
    try:
        interval = int(value)
        if interval < 50 or interval > 10000:
            raise ValidationError(_("L'intervalle BFD doit être compris entre 50 et 10000 ms"), code='invalid_bfd_interval')
        return interval
    except (ValueError, TypeError):
        raise ValidationError(_("L'intervalle BFD doit être un nombre entier"), code='invalid_bfd_interval_type')


# ============================================================================
# VALIDATEURS POUR ALERTES ET SEUILS
# ============================================================================

def validate_alert_threshold(value, min_val=None, max_val=None):
    """
    Valide un seuil d'alerte (CPU %, température °C, SNR dB, etc.) avec bornes optionnelles
    """
    if value is None:
        return value
    
    try:
        thresh = float(value)
        if min_val is not None and thresh < min_val:
            raise ValidationError(_(f"Le seuil ne peut être inférieur à {min_val}"), code='threshold_too_low')
        if max_val is not None and thresh > max_val:
            raise ValidationError(_(f"Le seuil ne peut être supérieur à {max_val}"), code='threshold_too_high')
        return thresh
    except (ValueError, TypeError):
        raise ValidationError(_("Le seuil doit être un nombre"), code='invalid_threshold')


# ============================================================================
# GÉNÉRIQUES
# ============================================================================

def validate_positive_integer(value):
    """Valide un entier positif"""
    if value is None:
        return value
    
    try:
        val = int(value)
        if val <= 0:
            raise ValueError
        return val
    except (ValueError, TypeError):
        raise ValidationError(_("La valeur doit être un entier positif"), code='invalid_positive_integer')


def validate_non_negative_integer(value):
    """Valide un entier non négatif"""
    if value is None:
        return value
    
    try:
        val = int(value)
        if val < 0:
            raise ValueError
        return val
    except (ValueError, TypeError):
        raise ValidationError(_("La valeur doit être un entier non négatif"), code='invalid_non_negative_integer')


def validate_percentage(value):
    """Valide un pourcentage (0-100)"""
    if value is None:
        return value
    
    try:
        val = float(value)
        if val < 0 or val > 100:
            raise ValueError
        return val
    except (ValueError, TypeError):
        raise ValidationError(_("Le pourcentage doit être entre 0 et 100"), code='invalid_percentage')


def validate_decimal_precision(value, max_digits=10, decimal_places=2):
    """Valide la précision décimale pour les mesures (température, puissance, SNR)"""
    if value is None:
        return value
    
    try:
        str_value = str(value)
        if '.' in str_value:
            _, decimals = str_value.split('.')
            if len(decimals) > decimal_places:
                raise ValidationError(
                    _(f"Maximum {decimal_places} décimales autorisées"),
                    code='too_many_decimals'
                )
        
        total_digits = len(str_value.replace('.', '').replace('-', ''))
        if total_digits > max_digits:
            raise ValidationError(
                _(f"Maximum {max_digits} chiffres autorisés"),
                code='too_many_digits'
            )
        
        return value
    except (ValueError, TypeError):
        raise ValidationError(_("La valeur doit être un nombre"), code='invalid_number')


def validate_domain_name(value):
    """Valide un nom de domaine (pour les services, URLs)"""
    if not value:
        return value
    
    pattern = r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$'
    if not re.match(pattern, value):
        raise ValidationError(_("Nom de domaine invalide"), code='invalid_domain')
    
    return value


def validate_url_safe(value):
    """Valide un slug URL-safe (pour les identifiants d'API, endpoints)"""
    if not value:
        return value
    
    pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
    if not re.match(pattern, value):
        raise ValidationError(
            _("Le slug doit contenir des lettres minuscules, chiffres et tirets"),
            code='invalid_slug'
        )
    
    return value


def validate_date_range(start_date, end_date):
    """Valide une plage de dates (start <= end)"""
    if start_date and end_date:
        if start_date > end_date:
            raise ValidationError(
                _("La date de début doit être antérieure à la date de fin"),
                code='invalid_date_range'
            )
    return True


def validate_timezone(value):
    """Valide un fuseau horaire (pour les logs et planifications)"""
    if not value:
        return value
    
    try:
        import pytz
        pytz.timezone(value)
        return value
    except ImportError:
        # Si pytz n'est pas installé, validation basique
        if value in ['UTC', 'Africa/Tunis', 'Europe/Paris']:
            return value
        raise ValidationError(_("Fuseau horaire invalide"), code='invalid_timezone')
    except pytz.UnknownTimeZoneError:
        raise ValidationError(_("Fuseau horaire inconnu"), code='unknown_timezone')


# ============================================================================
# VALIDATEURS DE FICHIERS (exports, configurations)
# ============================================================================

def validate_file_size(value, max_size_mb=10):
    """Valide la taille d'un fichier (max_size_mb par défaut 10 Mo)"""
    if not value:
        return value
    
    if value.size > max_size_mb * 1024 * 1024:
        raise ValidationError(
            _(f"La taille du fichier ne doit pas dépasser {max_size_mb} MB"),
            code='file_too_large'
        )
    
    return value


def validate_file_extension(value, allowed_extensions=None):
    """Valide l'extension d'un fichier (exports CSV, PDF, XLSX, JSON)"""
    if not value:
        return value
    
    allowed = allowed_extensions or ['.csv', '.pdf', '.xlsx', '.json']
    import os
    
    ext = os.path.splitext(value.name)[1].lower()
    
    if ext not in allowed:
        raise ValidationError(
            _(f"Extension de fichier non supportée. Extensions autorisées: {', '.join(allowed)}"),
            code='invalid_extension'
        )
    
    return value


# ============================================================================
# VALIDATEURS DE MODÈLES (unicité)
# ============================================================================

def validate_unique_field(model, field_name, value, exclude_id=None):
    """Valide l'unicité d'un champ dans un modèle Django"""
    if not value:
        return value
    
    kwargs = {field_name: value}
    if exclude_id:
        queryset = model.objects.exclude(id=exclude_id)
    else:
        queryset = model.objects.all()
    
    if queryset.filter(**kwargs).exists():
        raise ValidationError(
            _(f"La valeur '{value}' existe déjà"),
            code='duplicate_value'
        )
    
    return value