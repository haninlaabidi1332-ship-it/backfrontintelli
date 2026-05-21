import os
from rest_framework import serializers
from .models import (
    KPIHistory, Report, DashboardWidget,
    NetworkDevice, TopologyLink, SSHMetricsSnapshot, NetworkTraffic,
)


class KPIHistorySerializer(serializers.ModelSerializer):
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True, allow_null=True)

    class Meta:
        model = KPIHistory
        exclude = ['id']


class ReportSerializer(serializers.ModelSerializer):
    generated_by_email    = serializers.CharField(source='generated_by.email',         read_only=True, allow_null=True)
    generated_by_fullname = serializers.CharField(source='generated_by.get_full_name', read_only=True, allow_null=True)
    download_url  = serializers.SerializerMethodField()
    file_size_kb  = serializers.SerializerMethodField()
    report_type_label = serializers.CharField(source='get_report_type_display', read_only=True)
    format_label      = serializers.CharField(source='get_format_display',      read_only=True)
    status_label      = serializers.CharField(source='get_status_display',      read_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 'name',
            'report_type', 'report_type_label',
            'format', 'format_label',
            'status', 'status_label',
            'date_from', 'date_to',
            'parameters',
            'generated_by', 'generated_by_email', 'generated_by_fullname',
            'generated_at',
            'error_message',
            'download_url', 'file_size_kb',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'status', 'generated_at', 'file',
            'generated_by', 'error_message',
            'created_at', 'updated_at',
        ]

    def get_download_url(self, obj):
        if obj.status != 'ready' or not obj.file or not obj.file.name:
            return None
        request = self.context.get('request')
        path = f"/api/v2/analytics/reports/{obj.id}/download/"
        if request:
            return request.build_absolute_uri(path)
        return path

    def get_file_size_kb(self, obj):
        if not obj.file or not obj.file.name:
            return None
        try:
            return round(obj.file.size / 1024, 1)
        except (FileNotFoundError, OSError):
            return None


class DashboardWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardWidget
        fields = '__all__'
        read_only_fields = ['id', 'user']


# ============================================================================
# NETWORK DEVICE
# ============================================================================

class NetworkDeviceSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(source='site.name', read_only=True)

    class Meta:
        model = NetworkDevice
        fields = [
            'id', 'name', 'device_type', 'ip_address', 'hostname',
            'site', 'site_name', 'auth_method', 'ssh_port', 'snmp_port',
            'is_active', 'is_reachable', 'last_connection_at', 'connection_error',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'is_reachable', 'last_connection_at', 'connection_error',
            'created_at', 'updated_at',
        ]
        extra_kwargs = {
            'ssh_password':    {'write_only': True},
            'ssh_key':         {'write_only': True},
            'snmp_community':  {'write_only': True},
        }


# ============================================================================
# TOPOLOGY LINK
# ============================================================================

class TopologyLinkSerializer(serializers.ModelSerializer):
    source_device_name      = serializers.CharField(source='source_device.name',      read_only=True)
    destination_device_name = serializers.CharField(source='destination_device.name', read_only=True)

    class Meta:
        model = TopologyLink
        fields = [
            'id',
            'source_device', 'source_device_name', 'source_interface',
            'destination_device', 'destination_device_name', 'destination_interface',
            'link_type', 'bandwidth_mbps', 'is_active', 'description',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# SSH METRICS SNAPSHOT
# ============================================================================

class SSHMetricsSnapshotSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.name', read_only=True)

    class Meta:
        model = SSHMetricsSnapshot
        fields = [
            'id', 'device', 'device_name', 'timestamp',
            'cpu_usage_pct', 'memory_usage_pct', 'memory_available_mb',
            'temperature_c', 'temperature_threshold_c',
            'optical_rx_power_dbm', 'optical_tx_power_dbm',
            'uptime_seconds', 'process_count', 'active_connections',
            'is_anomaly', 'collection_duration_ms',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# NETWORK TRAFFIC
# ============================================================================

class NetworkTrafficSerializer(serializers.ModelSerializer):
    interface_name  = serializers.CharField(source='interface.name',  read_only=True, allow_null=True)
    fiber_link_name = serializers.CharField(source='fiber_link.name', read_only=True, allow_null=True)

    class Meta:
        model = NetworkTraffic
        fields = [
            'id', 'interface', 'interface_name', 'fiber_link', 'fiber_link_name',
            'timestamp',
            'bytes_in', 'bytes_out', 'packets_in', 'packets_out',
            'errors_in', 'errors_out', 'dropped_packets',
            'throughput_mbps', 'utilization_pct',
            'is_congested', 'is_anomaly',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
