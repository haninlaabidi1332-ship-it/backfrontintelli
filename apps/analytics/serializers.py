from rest_framework import serializers
from .models import KPIHistory, Report, DashboardWidget

class KPIHistorySerializer(serializers.ModelSerializer):
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True, allow_null=True)
    class Meta:
        model = KPIHistory
        exclude = ['id']

class ReportSerializer(serializers.ModelSerializer):
    generated_by_email = serializers.CharField(source='generated_by.email', read_only=True)
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ['id', 'generated_at', 'status', 'file']

class DashboardWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardWidget
        fields = '__all__'
        read_only_fields = ['id', 'user']