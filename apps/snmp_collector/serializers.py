from rest_framework import serializers
from .models import (
    SnmpOID, PollingProfile, DeviceProfile, ProfileOID,
    MetricHistory, PollJob, SnmpErrorLog, SnmpThresholdRule, SnmpAlert
)


class SnmpOIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = SnmpOID
        fields = ['id', 'name', 'oid', 'description', 'unit', 'data_type', 'scale_factor', 'is_active']


class PollingProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollingProfile
        fields = '__all__'


class ProfileOIDSerializer(serializers.ModelSerializer):
    oid_name = serializers.CharField(source='oid.name', read_only=True)

    class Meta:
        model = ProfileOID
        fields = ['id', 'profile', 'oid', 'oid_name', 'is_critical', 'order']


class DeviceProfileSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    device_type_model = serializers.CharField(source='device_type.model', read_only=True)
    profile_oids = ProfileOIDSerializer(many=True, read_only=True)

    class Meta:
        model = DeviceProfile
        fields = [
            'id', 'name', 'vendor', 'vendor_name', 'device_type', 'device_type_model',
            'sys_object_id', 'polling_profile', 'is_active', 'description', 'profile_oids'
        ]


class MetricHistorySerializer(serializers.ModelSerializer):
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True)
    oid_name = serializers.CharField(source='oid.name', read_only=True)
    oid_unit = serializers.CharField(source='oid.unit', read_only=True)
    interface_name = serializers.CharField(source='interface.name', read_only=True, allow_null=True)
    ont_serial = serializers.CharField(source='ont.serial_number', read_only=True, allow_null=True)

    class Meta:
        model = MetricHistory
        fields = [
            'id', 'olt', 'olt_hostname', 'oid', 'oid_name', 'oid_unit',
            'interface', 'interface_name', 'ont', 'ont_serial',
            'raw_value', 'numeric_value', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class PollJobSerializer(serializers.ModelSerializer):
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True)
    duration_ms = serializers.IntegerField(read_only=True)
    success_rate = serializers.SerializerMethodField()

    class Meta:
        model = PollJob
        fields = [
            'id', 'olt', 'olt_hostname', 'profile', 'state', 'started_at', 'finished_at',
            'duration_ms', 'metrics_collected', 'metrics_failed',
            'success_rate', 'error_message', 'created_at'
        ]

    def get_success_rate(self, obj):
        total = obj.metrics_collected + obj.metrics_failed
        return round(obj.metrics_collected / total * 100, 1) if total else None


class SnmpErrorLogSerializer(serializers.ModelSerializer):
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True)
    oid_name = serializers.CharField(source='oid.name', read_only=True, allow_null=True)

    class Meta:
        model = SnmpErrorLog
        fields = ['id', 'olt', 'olt_hostname', 'oid', 'oid_name',
                  'error_type', 'error_message', 'occurred_at', 'resolved']


class SnmpThresholdRuleSerializer(serializers.ModelSerializer):
    oid_name = serializers.CharField(source='oid.name', read_only=True)
    oid_unit = serializers.CharField(source='oid.unit', read_only=True)

    class Meta:
        model = SnmpThresholdRule
        fields = [
            'id', 'name', 'oid', 'oid_name', 'oid_unit',
            'operator', 'threshold', 'severity', 'message', 'is_active', 'cooldown_minutes'
        ]


class SnmpAlertSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True)
    acknowledged_by_email = serializers.CharField(source='acknowledged_by.email', read_only=True, allow_null=True)

    class Meta:
        model = SnmpAlert
        fields = [
            'id', 'rule', 'rule_name', 'olt', 'olt_hostname',
            'value', 'message', 'severity', 'status',
            'first_seen', 'last_seen', 'acknowledged_by',
            'acknowledged_by_email', 'acknowledged_at', 'cleared_at'
        ]
        read_only_fields = ['id', 'first_seen', 'last_seen']