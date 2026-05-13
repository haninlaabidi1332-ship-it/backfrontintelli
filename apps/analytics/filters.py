import django_filters
from .models import KPIHistory

class KPIHistoryFilter(django_filters.FilterSet):
    period = django_filters.ChoiceFilter(choices=KPIHistory.Period.choices)
    olt = django_filters.UUIDFilter()
    timestamp_after = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    timestamp_before = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')
    class Meta:
        model = KPIHistory
        fields = ['period', 'olt']