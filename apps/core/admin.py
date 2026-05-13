# apps/core/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from import_export.admin import ImportExportModelAdmin
from import_export import resources
import json

from .models import Config


# ============================================================================
# RESSOURCE POUR IMPORT/EXPORT
# ============================================================================

class ConfigResource(resources.ModelResource):
    """Resource pour l'import/export des configurations IntelliOLT"""
    
    class Meta:
        model = Config
        fields = ('id', 'key', 'config_type', 'is_encrypted', 'created_at', 'updated_at')
        export_order = fields


# ============================================================================
# ADMIN DE LA CONFIGURATION
# ============================================================================

@admin.register(Config)
class ConfigAdmin(ImportExportModelAdmin):
    """
    Administration des configurations globales IntelliOLT – AI-Powered Fiber Network Supervision Platform
    """
    resource_class = ConfigResource
    
    # Liste
    list_display = [
        'key_display', 'config_type_badge', 'value_preview', 
        'encrypted_indicator', 'created_at'
    ]
    list_display_links = ['key_display']
    
    # Filtres
    list_filter = ['config_type', 'is_encrypted', 'created_at']
    
    # Recherche
    search_fields = ['key', 'description', 'value']
    
    # Organisation
    date_hierarchy = 'created_at'
    list_per_page = 25
    save_on_top = True
    
    # Champs
    fieldsets = (
        ('⚙️ Configuration IntelliOLT', {
            'fields': ('key', 'config_type', 'description')
        }),
        ('📊 Valeur', {
            'fields': ('value',),
            'description': '''
                <div class="alert alert-info">
                    <strong>Format JSON :</strong> La valeur doit être au format JSON valide.
                    <br><strong>Exemples :</strong> 
                    <code>{"snmp_community": "public", "polling_interval": 60}</code>, 
                    <code>["OLT-01", "OLT-02"]</code>, 
                    <code>42</code>, 
                    <code>{"bfd_tx": 100, "bfd_rx": 100}</code>
                </div>
            '''
        }),
        ('🔒 Sécurité', {
            'fields': ('is_encrypted',),
            'classes': ('collapse',)
        }),
        ('📈 Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'value_formatted']
    
    # ========================================================================
    # MÉTHODES D'AFFICHAGE
    # ========================================================================
    
    def key_display(self, obj):
        """Affiche la clé avec icône selon le type de configuration"""
        icons = {
            'general': '⚙️',
            'security': '🛡️',
            'snmp': '📊',
            'bfd': '🔗',
            'alerting': '🚨',
            'ai_engine': '🧠',
            'eve_ng': '🧪',
            'notifications': '🔔',
            'exports': '📁',
            'logs': '📜',
        }
        icon = icons.get(obj.config_type, '📊')
        return format_html(
            '<strong>{} {}</strong><br><small class="text-muted">{}</small>',
            icon, obj.key, obj.description[:50] + '...' if obj.description else ''
        )
    key_display.short_description = 'Configuration'
    key_display.admin_order_field = 'key'
    
    def config_type_badge(self, obj):
        """Badge pour le type de configuration avec couleurs adaptées à IntelliOLT"""
        colors = {
            'general': 'secondary',
            'security': 'danger',
            'snmp': 'primary',
            'bfd': 'info',
            'alerting': 'warning',
            'ai_engine': 'dark',
            'eve_ng': 'success',
            'notifications': 'primary',
            'exports': 'secondary',
            'logs': 'secondary',
        }
        color = colors.get(obj.config_type, 'secondary')
        
        # Traduction des types en français
        type_labels = {
            'general': 'Général',
            'security': 'Sécurité',
            'snmp': 'SNMP (collecte, OIDs)',
            'bfd': 'BFD (détection panne rapide)',
            'alerting': 'Alertes (seuils, notifications)',
            'ai_engine': 'IA / Machine Learning',
            'eve_ng': 'EVE-NG (simulation)',
            'notifications': 'Notifications',
            'exports': 'Exports',
            'logs': 'Journalisation',
        }
        label = type_labels.get(obj.config_type, obj.get_config_type_display())
        
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, label
        )
    config_type_badge.short_description = 'Type'
    config_type_badge.admin_order_field = 'config_type'
    
    def value_preview(self, obj):
        """Aperçu de la valeur avec formatage compact"""
        try:
            if isinstance(obj.value, dict):
                keys = list(obj.value.keys())
                if len(keys) > 3:
                    preview = ', '.join(keys[:3]) + f' +{len(keys)-3}'
                else:
                    preview = ', '.join(keys)
                return f"{{ {preview} }}"
            elif isinstance(obj.value, list):
                return f"[{len(obj.value)} éléments]"
            else:
                value_str = str(obj.value)
                if len(value_str) > 50:
                    return value_str[:50] + '...'
                return value_str
        except:
            return '⚠️ Erreur de format'
    value_preview.short_description = 'Valeur'
    
    def encrypted_indicator(self, obj):
        """Indicateur de chiffrement"""
        if obj.is_encrypted:
            return format_html('<span class="badge bg-warning" title="Donnée chiffrée">🔒 Chiffré</span>')
        return format_html('<span class="badge bg-success" title="Donnée en clair">🔓 Clair</span>')
    encrypted_indicator.short_description = 'Sécurité'
    
    def value_formatted(self, obj):
        """Affiche la valeur formatée en JSON avec style"""
        try:
            if isinstance(obj.value, (dict, list)):
                return format_html(
                    '<pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; font-size: 12px;">{}</pre>',
                    json.dumps(obj.value, indent=2, ensure_ascii=False)
                )
            else:
                return format_html(
                    '<code>{}</code>',
                    obj.value
                )
        except:
            return format_html(
                '<span class="text-danger">Erreur de format JSON</span>'
            )
    value_formatted.short_description = 'Valeur (formatée)'
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def save_model(self, request, obj, form, change):
        """Validation avant sauvegarde (règles métier IntelliOLT)"""
        try:
            # S'assurer que la valeur est un JSON valide
            if isinstance(obj.value, str):
                try:
                    obj.value = json.loads(obj.value)
                except json.JSONDecodeError:
                    pass
            
            # Validation spécifique selon le type de configuration
            if obj.config_type == 'snmp' and isinstance(obj.value, dict):
                # Exemple : vérifier que les intervalles de polling sont positifs
                if 'polling_interval' in obj.value and obj.value['polling_interval'] < 10:
                    raise ValueError("L'intervalle SNMP doit être ≥ 10 secondes")
            
            elif obj.config_type == 'bfd' and isinstance(obj.value, dict):
                if 'tx_interval' in obj.value and obj.value['tx_interval'] < 50:
                    raise ValueError("L'intervalle BFD TX doit être ≥ 50 ms")
                if 'rx_interval' in obj.value and obj.value['rx_interval'] < 50:
                    raise ValueError("L'intervalle BFD RX doit être ≥ 50 ms")
            
            elif obj.config_type == 'alerting' and isinstance(obj.value, dict):
                if 'threshold' in obj.value and obj.value['threshold'] < 0:
                    raise ValueError("Le seuil d'alerte ne peut être négatif")
            
            elif obj.config_type == 'ai_engine' and isinstance(obj.value, dict):
                if 'anomaly_score_threshold' in obj.value and not (0 <= obj.value['anomaly_score_threshold'] <= 1):
                    raise ValueError("Le seuil de score d'anomalie doit être compris entre 0 et 1")
            
            super().save_model(request, obj, form, change)
            
            action = 'modifiée' if change else 'créée'
            self.message_user(
                request, 
                f'✅ Configuration "{obj.key}" {action} avec succès.',
                messages.SUCCESS
            )
            
        except Exception as e:
            self.message_user(
                request,
                f'❌ Erreur : {str(e)}',
                messages.ERROR
            )
    
    # ========================================================================
    # ACTIONS PERSONNALISÉES
    # ========================================================================
    
    actions = ['duplicate_config', 'export_selected', 'toggle_encryption', 'validate_configs']
    
    def duplicate_config(self, request, queryset):
        """Duplique une configuration"""
        for config in queryset:
            new_key = f"{config.key}_copie"
            count = 1
            while Config.objects.filter(key=new_key).exists():
                count += 1
                new_key = f"{config.key}_copie_{count}"
            
            Config.objects.create(
                key=new_key,
                value=config.value,
                description=f"Copie de {config.key}",
                config_type=config.config_type,
                is_encrypted=config.is_encrypted
            )
        
        self.message_user(
            request,
            f'✅ {queryset.count()} configuration(s) dupliquée(s).',
            messages.SUCCESS
        )
    duplicate_config.short_description = "📋 Dupliquer la sélection"
    
    def export_selected(self, request, queryset):
        """Export JSON des configurations sélectionnées"""
        from django.http import HttpResponse
        
        data = []
        for config in queryset:
            data.append({
                'key': config.key,
                'value': config.value,
                'description': config.description,
                'config_type': config.config_type,
                'config_type_display': config.get_config_type_display(),
                'is_encrypted': config.is_encrypted,
                'created_at': config.created_at.isoformat() if config.created_at else None,
                'updated_at': config.updated_at.isoformat() if config.updated_at else None,
            })
        
        response = HttpResponse(
            json.dumps(data, indent=2, default=str, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename="intelliolt_configurations.json"'
        return response
    export_selected.short_description = "📤 Exporter la sélection"
    
    def toggle_encryption(self, request, queryset):
        """Active/désactive le chiffrement"""
        count = 0
        for config in queryset:
            config.is_encrypted = not config.is_encrypted
            config.save()
            count += 1
        
        self.message_user(
            request,
            f'🔄 Statut de chiffrement modifié pour {count} configuration(s).',
            messages.SUCCESS
        )
    toggle_encryption.short_description = "🔄 Basculer chiffrement"
    
    def validate_configs(self, request, queryset):
        """Valide les configurations sélectionnées selon les règles IntelliOLT"""
        errors = []
        warnings = []
        
        for config in queryset:
            # Validation générique de base (JSON valide)
            if not isinstance(config.value, (dict, list, str, int, float, bool)):
                errors.append(f"{config.key}: valeur de type non supporté")
                continue
            
            # Validations spécifiques
            if config.config_type == 'snmp' and isinstance(config.value, dict):
                if 'polling_interval' in config.value and config.value['polling_interval'] < 10:
                    warnings.append(f"{config.key}: polling_interval très petit (<10s)")
            
            elif config.config_type == 'bfd' and isinstance(config.value, dict):
                if 'tx_interval' in config.value and config.value['tx_interval'] < 50:
                    warnings.append(f"{config.key}: intervalle TX BFD anormalement bas")
            
            elif config.config_type == 'alerting' and isinstance(config.value, dict):
                if 'threshold' in config.value and config.value['threshold'] < 0:
                    errors.append(f"{config.key}: seuil d'alerte négatif")
            
            elif config.config_type == 'ai_engine' and isinstance(config.value, dict):
                if 'anomaly_score_threshold' in config.value:
                    if config.value['anomaly_score_threshold'] < 0 or config.value['anomaly_score_threshold'] > 1:
                        errors.append(f"{config.key}: seuil de score d'anomalie hors plage [0-1]")
        
        if errors:
            self.message_user(
                request,
                f'❌ Erreurs:\n' + '\n'.join(errors),
                messages.ERROR
            )
        elif warnings:
            self.message_user(
                request,
                f'⚠️ Avertissements:\n' + '\n'.join(warnings),
                messages.WARNING
            )
        else:
            self.message_user(
                request,
                f'✅ Toutes les configurations sont valides.',
                messages.SUCCESS
            )
    validate_configs.short_description = "✅ Valider la sélection"
    
    # ========================================================================
    # PERMISSIONS
    # ========================================================================
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:
            readonly.append('key')
        return readonly
    
    def has_delete_permission(self, request, obj=None):
        # Clés critiques pour IntelliOLT
        critical_keys = [
            'system.security.jwt_secret',
            'database.connection',
            'notifications.email_config',
            'snmp.default_community',
            'bfd.default_intervals',
            'ai_engine.active_model_path',
            'alerting.global_rules',
        ]
        if obj and obj.key in critical_keys:
            return False
        return super().has_delete_permission(request, obj)


# ============================================================================
# CONFIGURATION DU TABLEAU DE BORD
# ============================================================================

class CoreDashboard:
    """
    Statistiques pour le tableau de bord IntelliOLT
    """
    
    @staticmethod
    def get_stats():
        """Récupère les statistiques des configurations IntelliOLT"""
        total_configs = Config.objects.count()
        
        configs_by_type = {}
        type_labels = {
            'general': 'Général',
            'security': 'Sécurité',
            'snmp': 'SNMP',
            'bfd': 'BFD',
            'alerting': 'Alertes',
            'ai_engine': 'IA / ML',
            'eve_ng': 'EVE-NG',
            'notifications': 'Notifications',
            'exports': 'Exports',
            'logs': 'Journalisation',
        }
        
        for config_type, _ in Config.CONFIG_TYPES:
            count = Config.objects.filter(config_type=config_type).count()
            if count > 0:
                label = type_labels.get(config_type, config_type)
                configs_by_type[label] = count
        
        encrypted_count = Config.objects.filter(is_encrypted=True).count()
        
        return {
            'total_configs': total_configs,
            'total_configs_display': f'{total_configs} configuration(s) IntelliOLT',
            'configs_by_type': configs_by_type,
            'encrypted_count': encrypted_count,
            'encrypted_percentage': round((encrypted_count / total_configs * 100) if total_configs > 0 else 0, 1),
        }


# Configuration de l'interface d'administration
admin.site.site_header = "IntelliOLT - Administration"
admin.site.site_title = "IntelliOLT Admin"
admin.site.index_title = "📊 Tableau de bord IntelliOLT - Supervision OLT avec IA"