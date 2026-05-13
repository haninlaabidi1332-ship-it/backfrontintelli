import django_filters
from django.db.models import Q
from .models import BFDSession, BFDActiveAlert, BFDThresholdRule


class BFDSessionFilter(django_filters.FilterSet):
    olt = django_filters.UUIDFilter(field_name='olt__id')
    link = django_filters.UUIDFilter()
    state = django_filters.ChoiceFilter(choices=BFDSession.State.choices)
    is_enabled = django_filters.BooleanFilter()
    is_monitored = django_filters.BooleanFilter()
    min_loss_rate = django_filters.NumberFilter(field_name='loss_rate_pct', lookup_expr='gte')
    max_loss_rate = django_filters.NumberFilter(field_name='loss_rate_pct', lookup_expr='lte')
    search = django_filters.CharFilter(method='filter_search')

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(peer_ip__icontains=value) |
            Q(description__icontains=value) |
            Q(link__name__icontains=value) |
            Q(olt__hostname__icontains=value)
        )

    class Meta:
        model = BFDSession
        fields = ['olt', 'link', 'state', 'is_enabled', 'is_monitored']


class BFDActiveAlertFilter(django_filters.FilterSet):
    session = django_filters.UUIDFilter()
    severity = django_filters.ChoiceFilter(choices=BFDThresholdRule.SEVERITY_CHOICES)
    status = django_filters.ChoiceFilter(choices=BFDActiveAlert.STATUS_CHOICES)

    class Meta:
        model = BFDActiveAlert
        fields = ['session', 'severity', 'status']