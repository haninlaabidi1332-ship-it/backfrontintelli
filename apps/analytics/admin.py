from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    KPIHistory, Report, DashboardWidget,
    NetworkDevice, TopologyLink, SSHMetricsSnapshot, NetworkTraffic,
)


def register_admin():

    # ========================================================================
    # KPI HISTORY
    # ========================================================================

    @admin.register(KPIHistory)
    class KPIHistoryAdmin(admin.ModelAdmin):
        list_display   = ['timestamp', 'period', 'olt', 'total_olts', 'active_olts',
                          'online_onts', 'avg_cpu_usage', 'snmp_success_rate', 'alert_count']
        list_filter    = ['period', 'olt']
        date_hierarchy = 'timestamp'
        readonly_fields = ['created_at', 'updated_at']

    # ========================================================================
    # REPORT
    # ========================================================================

    def _generate_reports_action(modeladmin, request, queryset):
        """Regénère les fichiers pour les rapports sélectionnés."""
        from .tasks import generate_report
        count = 0
        for report in queryset.exclude(status='generating'):
            report.status = 'pending'
            report.error_message = ''
            report.save(update_fields=['status', 'error_message'])
            generate_report.delay(str(report.id))
            count += 1
        modeladmin.message_user(request, f"{count} rapport(s) en cours de génération.")

    _generate_reports_action.short_description = "🔄 Regénérer les rapports sélectionnés"

    @admin.register(Report)
    class ReportAdmin(admin.ModelAdmin):
        list_display   = ['name', 'report_type', 'format', '_status_badge',
                          'generated_by', 'generated_at', '_download_link', '_file_size']
        list_filter    = ['report_type', 'status', 'format']
        search_fields  = ['name']
        readonly_fields = ['generated_at', 'file', 'status', 'error_message',
                           'created_at', 'updated_at', '_download_link']
        date_hierarchy = 'created_at'
        actions        = [_generate_reports_action]

        fieldsets = (
            ('Identification', {
                'fields': ('name', 'report_type', 'format', 'parameters'),
            }),
            ('Période', {
                'fields': ('date_from', 'date_to'),
            }),
            ('Génération', {
                'fields': ('status', 'generated_by', 'generated_at',
                           'file', '_download_link', 'error_message'),
            }),
            ('Horodatage', {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',),
            }),
        )

        def _status_badge(self, obj):
            colors = {
                'pending':    ('#6c757d', '⏳ En attente'),
                'generating': ('#fd7e14', '⚙️ En cours'),
                'ready':      ('#28a745', '✅ Prêt'),
                'failed':     ('#dc3545', '❌ Échec'),
            }
            color, label = colors.get(obj.status, ('#6c757d', obj.status))
            return format_html(
                '<span style="color:{};font-weight:bold">{}</span>',
                color, label,
            )
        _status_badge.short_description = 'Statut'
        _status_badge.admin_order_field = 'status'

        def _download_link(self, obj):
            if obj.status == 'ready' and obj.file and obj.file.name:
                url = f"/api/v2/analytics/reports/{obj.id}/download/"
                ext = obj.format.upper()
                return format_html(
                    '<a href="{}" target="_blank" '
                    'style="background:#1e3a5f;color:white;padding:3px 8px;'
                    'border-radius:4px;text-decoration:none">⬇ {}</a>',
                    url, ext,
                )
            if obj.status == 'failed':
                return format_html(
                    '<span style="color:#dc3545">Échec : {}</span>',
                    obj.error_message[:80] if obj.error_message else '—',
                )
            return format_html('<span style="color:#999">—</span>')
        _download_link.short_description = 'Télécharger'

        def _file_size(self, obj):
            if not obj.file or not obj.file.name:
                return '—'
            try:
                kb = obj.file.size / 1024
                return f"{kb:.1f} Ko" if kb < 1024 else f"{kb/1024:.1f} Mo"
            except (FileNotFoundError, OSError):
                return 'Fichier manquant'
        _file_size.short_description = 'Taille'

    # ========================================================================
    # DASHBOARD WIDGET
    # ========================================================================

    @admin.register(DashboardWidget)
    class DashboardWidgetAdmin(admin.ModelAdmin):
        list_display = ['name', 'user', 'widget_type', 'order', 'is_active']
        list_filter  = ['widget_type', 'is_active']
        search_fields = ['name', 'user__email']

    # ========================================================================
    # NETWORK DEVICE
    # ========================================================================

    @admin.register(NetworkDevice)
    class NetworkDeviceAdmin(admin.ModelAdmin):
        list_display   = ['name', 'device_type', 'ip_address', 'site',
                          'is_active', '_reachable_badge', 'last_connection_at']
        list_filter    = ['device_type', 'site', 'is_active', 'is_reachable', 'auth_method']
        search_fields  = ['name', 'hostname', 'ip_address']
        readonly_fields = ['is_reachable', 'last_connection_at', 'connection_error',
                           'created_at', 'updated_at']

        fieldsets = (
            ('Identification', {'fields': ('name', 'device_type', 'hostname')}),
            ('Localisation',   {'fields': ('ip_address', 'site')}),
            ('Méthode SSH',    {'fields': ('auth_method', 'ssh_username', 'ssh_password',
                                           'ssh_port', 'ssh_key')}),
            ('SNMP',           {'fields': ('snmp_community', 'snmp_port')}),
            ('État',           {'fields': ('is_active', 'is_reachable',
                                           'last_connection_at', 'connection_error')}),
            ('Horodatage',     {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
        )

        def _reachable_badge(self, obj):
            if obj.is_reachable:
                return format_html('<span style="color:#28a745;font-weight:bold">✓ Accessible</span>')
            return format_html('<span style="color:#dc3545;font-weight:bold">✗ Inaccessible</span>')
        _reachable_badge.short_description = 'Accessibilité'

    # ========================================================================
    # TOPOLOGY LINK
    # ========================================================================

    @admin.register(TopologyLink)
    class TopologyLinkAdmin(admin.ModelAdmin):
        list_display   = ['source_device', 'source_interface',
                          'destination_device', 'destination_interface',
                          'link_type', 'bandwidth_mbps', 'is_active']
        list_filter    = ['link_type', 'is_active']
        search_fields  = ['source_device__name', 'destination_device__name']
        raw_id_fields  = ['source_device', 'destination_device']

    # ========================================================================
    # SSH METRICS SNAPSHOT
    # ========================================================================

    @admin.register(SSHMetricsSnapshot)
    class SSHMetricsSnapshotAdmin(admin.ModelAdmin):
        list_display   = ['device', 'timestamp', 'cpu_usage_pct',
                          'memory_usage_pct', 'temperature_c', '_anomaly_badge']
        list_filter    = ['device', 'is_anomaly']
        search_fields  = ['device__name']
        readonly_fields = ['timestamp', 'device', 'is_anomaly', 'created_at', 'updated_at']
        date_hierarchy  = 'timestamp'

        fieldsets = (
            ('Source',       {'fields': ('device', 'timestamp')}),
            ('CPU & Mémoire',{'fields': ('cpu_usage_pct', 'memory_usage_pct', 'memory_available_mb')}),
            ('Thermique',    {'fields': ('temperature_c', 'temperature_threshold_c')}),
            ('Optique',      {'fields': ('optical_rx_power_dbm', 'optical_tx_power_dbm')}),
            ('Système',      {'fields': ('uptime_seconds', 'process_count', 'active_connections')}),
            ('Détection',    {'fields': ('is_anomaly', 'collection_duration_ms')}),
        )

        def _anomaly_badge(self, obj):
            if obj.is_anomaly:
                return format_html('<span style="color:#dc3545;font-weight:bold">⚠ Anomalie</span>')
            return format_html('<span style="color:#28a745">✓ Normal</span>')
        _anomaly_badge.short_description = 'Statut'

    # ========================================================================
    # NETWORK TRAFFIC
    # ========================================================================

    @admin.register(NetworkTraffic)
    class NetworkTrafficAdmin(admin.ModelAdmin):
        list_display   = ['_source_name', 'timestamp', 'throughput_mbps',
                          'utilization_pct', 'is_congested', 'is_anomaly']
        list_filter    = ['is_congested', 'is_anomaly']
        search_fields  = ['interface__name', 'fiber_link__name']
        readonly_fields = ['timestamp', 'created_at', 'updated_at']
        date_hierarchy  = 'timestamp'

        fieldsets = (
            ('Source',      {'fields': ('interface', 'fiber_link', 'timestamp')}),
            ('Trafic',      {'fields': ('bytes_in', 'bytes_out', 'packets_in', 'packets_out')}),
            ('Erreurs',     {'fields': ('errors_in', 'errors_out', 'dropped_packets')}),
            ('Performance', {'fields': ('throughput_mbps', 'utilization_pct')}),
            ('État',        {'fields': ('is_congested', 'is_anomaly')}),
        )

        def _source_name(self, obj):
            if obj.interface:
                return obj.interface.name
            if obj.fiber_link:
                return obj.fiber_link.name
            return '—'
        _source_name.short_description = 'Source'
