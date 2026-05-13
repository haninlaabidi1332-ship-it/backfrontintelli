import django_filters
from .models import MetricHistory, SnmpAlert, SnmpThresholdRule


class MetricHistoryFilter(django_filters.FilterSet):
    olt = django_filters.UUIDFilter()
    oid = django_filters.UUIDFilter()
    interface = django_filters.UUIDFilter()
    ont = django_filters.UUIDFilter()
    timestamp_after = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    timestamp_before = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')
    value_min = django_filters.NumberFilter(field_name='numeric_value', lookup_expr='gte')
    value_max = django_filters.NumberFilter(field_name='numeric_value', lookup_expr='lte')

    class Meta:
        model = MetricHistory
        fields = ['olt', 'oid', 'interface', 'ont']


class SnmpAlertFilter(django_filters.FilterSet):
    olt = django_filters.UUIDFilter()
    rule = django_filters.UUIDFilter()
    severity = django_filters.ChoiceFilter(choices=SnmpThresholdRule.SEVERITY_CHOICES)
    status = django_filters.ChoiceFilter(choices=SnmpAlert.STATUS_CHOICES)
    created_after = django_filters.DateTimeFilter(field_name='first_seen', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='first_seen', lookup_expr='lte')

    class Meta:
        model = SnmpAlert
        fields = ['olt', 'rule', 'severity', 'status']