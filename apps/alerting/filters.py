import django_filters
from .models import Alert

class AlertFilter(django_filters.FilterSet):
    olt = django_filters.UUIDFilter()
    ont = django_filters.UUIDFilter()
    severity = django_filters.ChoiceFilter(choices=Alert.Severity.choices)
    status = django_filters.ChoiceFilter(choices=Alert.Status.choices)
    created_after = django_filters.DateTimeFilter(field_name='first_seen', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='first_seen', lookup_expr='lte')
    class Meta:
        model = Alert
        fields = ['olt', 'ont', 'severity', 'status']