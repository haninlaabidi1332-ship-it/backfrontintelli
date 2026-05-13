from django.contrib import admin
from django.utils.html import format_html

def register_admin():
    from .models import (
        SnmpOID, PollingProfile, DeviceProfile, ProfileOID,
        MetricHistory, PollJob, SnmpErrorLog, SnmpThresholdRule, SnmpAlert
    )

    @admin.register(SnmpOID)
    class SnmpOIDAdmin(admin.ModelAdmin):
        list_display = ['name', 'oid', 'data_type', 'unit', 'scale_factor', 'is_active']
        list_filter = ['data_type', 'is_active']
        search_fields = ['name', 'oid']
        ordering = ['name']

    @admin.register(PollingProfile)
    class PollingProfileAdmin(admin.ModelAdmin):
        list_display = ['name', 'timeout_seconds', 'retries', 'bulk_max_repetitions', 'is_default']
        list_filter = ['is_default']

    @admin.register(DeviceProfile)
    class DeviceProfileAdmin(admin.ModelAdmin):
        list_display = ['name', 'vendor', 'device_type', 'is_active']
        list_filter = ['vendor', 'is_active']
        search_fields = ['name', 'sys_object_id']
        raw_id_fields = ['vendor', 'device_type', 'polling_profile']

    @admin.register(ProfileOID)
    class ProfileOIDAdmin(admin.ModelAdmin):
        list_display = ['profile', 'oid', 'is_critical', 'order']
        list_filter = ['profile', 'is_critical']
        raw_id_fields = ['profile', 'oid']

    @admin.register(MetricHistory)
    class MetricHistoryAdmin(admin.ModelAdmin):
        list_display = ['olt', 'oid', 'numeric_value', 'timestamp']
        list_filter = ['oid', 'timestamp']
        search_fields = ['olt__hostname']
        ordering = ['-timestamp']
        readonly_fields = ['timestamp']
        raw_id_fields = ['olt', 'oid', 'interface', 'ont', 'gpon_port']

    @admin.register(PollJob)
    class PollJobAdmin(admin.ModelAdmin):
        list_display = ['olt', 'state', 'metrics_collected', 'metrics_failed', 'started_at']
        list_filter = ['state']
        search_fields = ['olt__hostname']
        ordering = ['-created_at']
        raw_id_fields = ['olt', 'profile']

    @admin.register(SnmpErrorLog)
    class SnmpErrorLogAdmin(admin.ModelAdmin):
        list_display = ['olt', 'error_type', 'occurred_at', 'resolved']
        list_filter = ['error_type', 'resolved']
        search_fields = ['olt__hostname', 'error_message']

    @admin.register(SnmpThresholdRule)
    class SnmpThresholdRuleAdmin(admin.ModelAdmin):
        list_display = ['name', 'oid', 'operator', 'threshold', 'severity', 'is_active']
        list_filter = ['severity', 'is_active']
        search_fields = ['name']

    @admin.register(SnmpAlert)
    class SnmpAlertAdmin(admin.ModelAdmin):
        list_display = ['rule', 'olt', 'value', 'severity', 'status', 'first_seen']
        list_filter = ['severity', 'status']
        search_fields = ['olt__hostname', 'rule__name']
        ordering = ['-first_seen']
        raw_id_fields = ['rule', 'olt', 'metric', 'acknowledged_by']