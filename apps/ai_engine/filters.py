import django_filters
from .models import AnomalyDetection, MLModel


class AnomalyDetectionFilter(django_filters.FilterSet):
    olt = django_filters.UUIDFilter()
    ont = django_filters.UUIDFilter()
    interface = django_filters.UUIDFilter()
    metric_name = django_filters.CharFilter(lookup_expr='icontains')
    severity = django_filters.ChoiceFilter(choices=AnomalyDetection.Severity.choices)
    resolved = django_filters.BooleanFilter()
    detected_after = django_filters.DateTimeFilter(field_name='detected_at', lookup_expr='gte')
    detected_before = django_filters.DateTimeFilter(field_name='detected_at', lookup_expr='lte')
    min_score = django_filters.NumberFilter(field_name='anomaly_score', lookup_expr='gte')
    max_score = django_filters.NumberFilter(field_name='anomaly_score', lookup_expr='lte')

    class Meta:
        model = AnomalyDetection
        fields = ['olt', 'ont', 'interface', 'metric_name', 'severity', 'resolved']