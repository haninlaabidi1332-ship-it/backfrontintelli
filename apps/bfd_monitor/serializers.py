from rest_framework import serializers
from .models import (
    BFDSession, BFDStateHistory, BFDPollingSchedule,
    BFDThresholdRule, BFDActiveAlert
)

class BFDSessionSerializer(serializers.ModelSerializer):
    link_name = serializers.CharField(source='link.name', read_only=True, allow_null=True)
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True, allow_null=True)
    interface_a_name = serializers.CharField(source='interface_a.name', read_only=True)
    interface_b_name = serializers.CharField(source='interface_b.name', read_only=True)
    state_display = serializers.CharField(source='get_state_display', read_only=True)
    detect_time_ms = serializers.IntegerField(read_only=True)
    availability_pct = serializers.FloatField(read_only=True)
    flap_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = BFDSession
        fields = [
            'id', 'name', 'description', 'link', 'link_name', 'olt', 'olt_hostname',
            'interface_a', 'interface_a_name', 'interface_b', 'interface_b_name',
            'peer_ip', 'local_ip', 'vrf', 'local_discriminator', 'remote_discriminator',
            'session_type', 'desired_tx_interval_ms', 'required_rx_interval_ms',
            'detection_multiplier', 'actual_tx_interval_ms', 'actual_rx_interval_ms',
            'state', 'state_display', 'diagnostic', 'last_state_change', 'uptime_seconds',
            'remote_state', 'packets_sent', 'packets_received', 'packets_lost',
            'loss_rate_pct', 'last_update', 'up_count', 'down_count', 'flap_count',
            'last_up_at', 'last_down_at', 'is_enabled', 'is_monitored',
            'detect_time_ms', 'availability_pct', 'flap_rate'
        ]
        read_only_fields = ['id', 'last_update', 'uptime_seconds', 'last_state_change',
                            'up_count', 'down_count', 'flap_count', 'last_up_at', 'last_down_at']

class BFDStateHistorySerializer(serializers.ModelSerializer):
    session_name = serializers.CharField(source='session.name', read_only=True)

    class Meta:
        model = BFDStateHistory
        fields = '__all__'
        read_only_fields = ['id', 'timestamp']

class BFDPollingScheduleSerializer(serializers.ModelSerializer):
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True)

    class Meta:
        model = BFDPollingSchedule
        fields = '__all__'

class BFDThresholdRuleSerializer(serializers.ModelSerializer):
    metric_display = serializers.CharField(source='get_metric_display', read_only=True)

    class Meta:
        model = BFDThresholdRule
        fields = '__all__'

class BFDActiveAlertSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    session_name = serializers.CharField(source='session.name', read_only=True)
    olt_hostname = serializers.SerializerMethodField()
    acknowledged_by_email = serializers.CharField(source='acknowledged_by.email', read_only=True, allow_null=True)

    class Meta:
        model = BFDActiveAlert
        fields = [
            'id', 'rule', 'rule_name', 'session', 'session_name', 'olt_hostname',
            'value', 'message', 'severity', 'status',
            'first_seen', 'last_seen', 'acknowledged_by',
            'acknowledged_by_email', 'acknowledged_at', 'cleared_at'
        ]
        read_only_fields = ['id', 'first_seen', 'last_seen']

    def get_olt_hostname(self, obj):
        if obj.session.olt:
            return obj.session.olt.hostname
        elif obj.session.link:
            return f"{obj.session.link.interface_a.olt.hostname}↔{obj.session.link.interface_b.olt.hostname}"
        return None