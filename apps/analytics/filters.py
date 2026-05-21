import django_filters
from .models import (
    KPIHistory, Report, NetworkDevice, TopologyLink,
    SSHMetricsSnapshot, NetworkTraffic,
)


class KPIHistoryFilter(django_filters.FilterSet):
    period           = django_filters.ChoiceFilter(choices=KPIHistory.Period.choices)
    olt              = django_filters.UUIDFilter()
    timestamp_after  = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    timestamp_before = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')

    class Meta:
        model  = KPIHistory
        fields = ['period', 'olt']


class ReportFilter(django_filters.FilterSet):
    report_type    = django_filters.ChoiceFilter(choices=Report.ReportType.choices)
    format         = django_filters.ChoiceFilter(choices=Report.Format.choices)
    status         = django_filters.ChoiceFilter(choices=Report.Status.choices)
    generated_by   = django_filters.UUIDFilter()
    name           = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    date_from_after  = django_filters.DateTimeFilter(field_name='date_from', lookup_expr='gte')
    date_from_before = django_filters.DateTimeFilter(field_name='date_from', lookup_expr='lte')
    date_to_after    = django_filters.DateTimeFilter(field_name='date_to',   lookup_expr='gte')
    date_to_before   = django_filters.DateTimeFilter(field_name='date_to',   lookup_expr='lte')
    created_after    = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before   = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model  = Report
        fields = ['report_type', 'format', 'status', 'generated_by']


class NetworkDeviceFilter(django_filters.FilterSet):
    name         = django_filters.CharFilter(field_name='name',     lookup_expr='icontains')
    hostname     = django_filters.CharFilter(field_name='hostname', lookup_expr='icontains')
    device_type  = django_filters.ChoiceFilter(choices=NetworkDevice.DeviceType.choices)
    site         = django_filters.UUIDFilter()
    is_active    = django_filters.BooleanFilter()
    is_reachable = django_filters.BooleanFilter()

    class Meta:
        model  = NetworkDevice
        fields = ['device_type', 'site', 'is_active', 'is_reachable']


class TopologyLinkFilter(django_filters.FilterSet):
    source_device      = django_filters.UUIDFilter()
    destination_device = django_filters.UUIDFilter()
    link_type          = django_filters.ChoiceFilter(choices=TopologyLink.LinkType.choices)
    is_active          = django_filters.BooleanFilter()
    bandwidth_min      = django_filters.NumberFilter(field_name='bandwidth_mbps', lookup_expr='gte')
    bandwidth_max      = django_filters.NumberFilter(field_name='bandwidth_mbps', lookup_expr='lte')

    class Meta:
        model  = TopologyLink
        fields = ['link_type', 'is_active']


class SSHMetricsSnapshotFilter(django_filters.FilterSet):
    device           = django_filters.UUIDFilter()
    timestamp_after  = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    timestamp_before = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')
    is_anomaly       = django_filters.BooleanFilter()
    cpu_usage_min    = django_filters.NumberFilter(field_name='cpu_usage_pct',    lookup_expr='gte')
    cpu_usage_max    = django_filters.NumberFilter(field_name='cpu_usage_pct',    lookup_expr='lte')
    memory_usage_min = django_filters.NumberFilter(field_name='memory_usage_pct', lookup_expr='gte')
    memory_usage_max = django_filters.NumberFilter(field_name='memory_usage_pct', lookup_expr='lte')

    class Meta:
        model  = SSHMetricsSnapshot
        fields = ['device', 'is_anomaly']


class NetworkTrafficFilter(django_filters.FilterSet):
    interface        = django_filters.UUIDFilter()
    fiber_link       = django_filters.UUIDFilter()
    timestamp_after  = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    timestamp_before = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')
    is_anomaly       = django_filters.BooleanFilter()
    is_congested     = django_filters.BooleanFilter()
    throughput_min   = django_filters.NumberFilter(field_name='throughput_mbps',  lookup_expr='gte')
    throughput_max   = django_filters.NumberFilter(field_name='throughput_mbps',  lookup_expr='lte')
    utilization_min  = django_filters.NumberFilter(field_name='utilization_pct',  lookup_expr='gte')
    utilization_max  = django_filters.NumberFilter(field_name='utilization_pct',  lookup_expr='lte')

    class Meta:
        model  = NetworkTraffic
        fields = ['is_anomaly', 'is_congested']
