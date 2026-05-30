from rest_framework import serializers
from .models import AlertRule, Alert, NotificationChannel

class AlertRuleSerializer(serializers.ModelSerializer):
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    class Meta:
        model = AlertRule
        fields = '__all__'

class AlertSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True, allow_null=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    acknowledged_by_email = serializers.CharField(source='acknowledged_by.email', read_only=True, allow_null=True)
    class Meta:
        model = Alert
        fields = '__all__'
        read_only_fields = ['id', 'first_seen', 'last_seen']

class NotificationChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationChannel
        fields = '__all__'