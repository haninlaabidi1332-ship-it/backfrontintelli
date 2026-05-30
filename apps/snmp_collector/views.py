from datetime import timedelta
from django.db.models import Avg, Min, Max, StdDev, Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated

from apps.core.pagination import StandardPagination, LargeResultsPagination
from apps.core.permissions import IsAdmin, IsSupervisor, IsOperator, CanViewSNMPMetrics, CanManageSNMPOID
from apps.core.responses import success_response, error_response

from .models import (
    SnmpOID, PollingProfile, DeviceProfile, ProfileOID,
    MetricHistory, PollJob, SnmpErrorLog, SnmpThresholdRule, SnmpAlert
)
from .serializers import (
    SnmpOIDSerializer, PollingProfileSerializer, DeviceProfileSerializer,
    ProfileOIDSerializer, MetricHistorySerializer, PollJobSerializer,
    SnmpErrorLogSerializer, SnmpThresholdRuleSerializer, SnmpAlertSerializer
)


class SnmpOIDViewSet(viewsets.ModelViewSet):
    queryset = SnmpOID.objects.all()
    serializer_class = SnmpOIDSerializer
    permission_classes = [IsAuthenticated, CanViewSNMPMetrics]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'oid', 'description']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageSNMPOID()]
        return [IsAuthenticated(), CanViewSNMPMetrics()]

    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request):
        oids = SnmpOID.objects.filter(is_active=True)
        serializer = SnmpOIDSerializer(oids, many=True)
        return success_response(serializer.data, f"{oids.count()} OIDs actifs")


class PollingProfileViewSet(viewsets.ModelViewSet):
    queryset = PollingProfile.objects.all()
    serializer_class = PollingProfileSerializer
    permission_classes = [IsAuthenticated, CanManageSNMPOID]
    pagination_class = StandardPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated(), IsOperator()]
        return [IsAuthenticated(), CanManageSNMPOID()]


class DeviceProfileViewSet(viewsets.ModelViewSet):
    queryset = DeviceProfile.objects.select_related(
        'vendor', 'device_type', 'polling_profile'
    ).prefetch_related('profile_oids__oid')
    serializer_class = DeviceProfileSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'sys_object_id']

    @action(detail=True, methods=['get'], url_path='oids')
    def oids(self, request, pk=None):
        profile = self.get_object()
        oids = ProfileOID.objects.filter(profile=profile).select_related('oid')
        serializer = ProfileOIDSerializer(oids, many=True)
        return success_response(serializer.data, "OIDs du profil")


class MetricHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MetricHistory.objects.select_related('olt', 'oid', 'interface')
    serializer_class = MetricHistorySerializer
    permission_classes = [IsAuthenticated, CanViewSNMPMetrics]
    pagination_class = LargeResultsPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering = ['-timestamp']

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if olt_id := params.get('olt'):
            qs = qs.filter(olt_id=olt_id)
        if oid_name := params.get('oid_name'):
            qs = qs.filter(oid__name=oid_name)
        if interface_id := params.get('interface'):
            qs = qs.filter(interface_id=interface_id)
        if hours := params.get('hours'):
            try:
                since = timezone.now() - timedelta(hours=float(hours))
                qs = qs.filter(timestamp__gte=since)
            except (TypeError, ValueError):
                pass
        return qs

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        olt_id = request.query_params.get('olt')
        oid_name = request.query_params.get('oid_name')
        hours = int(request.query_params.get('hours', 24))
        if not olt_id or not oid_name:
            return error_response("Paramètres 'olt' et 'oid_name' requis.", status_code=400)
        since = timezone.now() - timedelta(hours=hours)
        qs = MetricHistory.objects.filter(
            olt_id=olt_id, oid__name=oid_name,
            timestamp__gte=since, numeric_value__isnull=False
        )
        agg = qs.aggregate(avg=Avg('numeric_value'), min=Min('numeric_value'),
                           max=Max('numeric_value'), std=StdDev('numeric_value'))
        return success_response({
            'olt_id': olt_id, 'oid_name': oid_name, 'hours': hours,
            'count': qs.count(),
            'avg': round(agg['avg'] or 0, 3),
            'min': agg['min'], 'max': agg['max'],
            'std': round(agg['std'] or 0, 4),
        }, "Statistiques métriques")

    @action(detail=False, methods=['get'], url_path='timeseries')
    def timeseries(self, request):
        olt_id = request.query_params.get('olt')
        oid_name = request.query_params.get('oid_name')
        hours = int(request.query_params.get('hours', 6))
        if not olt_id or not oid_name:
            return error_response("Paramètres 'olt' et 'oid_name' requis.", status_code=400)
        since = timezone.now() - timedelta(hours=hours)
        data = list(MetricHistory.objects.filter(
            olt_id=olt_id, oid__name=oid_name,
            timestamp__gte=since, numeric_value__isnull=False
        ).order_by('timestamp').values('timestamp', 'numeric_value'))
        return success_response(data, f"{len(data)} points de données")

    @action(detail=False, methods=['get'], url_path='latest')
    def latest(self, request):
        from django.db.models import OuterRef, Subquery
        olt_id = request.query_params.get('olt')
        base = MetricHistory.objects.all()
        if olt_id:
            base = base.filter(olt_id=olt_id)
        latest_ids = base.filter(
            olt=OuterRef('olt'), oid=OuterRef('oid')
        ).order_by('-timestamp').values('id')[:1]
        metrics = MetricHistory.objects.filter(
            id__in=Subquery(latest_ids)
        ).select_related('oid', 'olt')
        if olt_id:
            metrics = metrics.filter(olt_id=olt_id)
        serializer = MetricHistorySerializer(metrics, many=True)
        return success_response(serializer.data, "Latest metrics")


class PollJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PollJob.objects.select_related('olt', 'profile')
    serializer_class = PollJobSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        if olt_id := self.request.query_params.get('olt'):
            qs = qs.filter(olt_id=olt_id)
        if state := self.request.query_params.get('state'):
            qs = qs.filter(state=state)
        return qs

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        qs = self.get_queryset()
        last_24h = timezone.now() - timedelta(hours=24)
        data = {
            'total_24h': qs.filter(created_at__gte=last_24h).count(),
            'by_state': dict(qs.filter(created_at__gte=last_24h)
                              .values_list('state').annotate(c=Count('id'))),
            'avg_metrics_per_job': qs.filter(created_at__gte=last_24h)
                                      .aggregate(avg=Avg('metrics_collected'))['avg'],
        }
        return success_response(data, "Résumé des jobs SNMP")


class SnmpErrorLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SnmpErrorLog.objects.select_related('olt', 'oid')
    serializer_class = SnmpErrorLogSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering = ['-occurred_at']

    def get_queryset(self):
        qs = super().get_queryset()
        if olt_id := self.request.query_params.get('olt'):
            qs = qs.filter(olt_id=olt_id)
        if error_type := self.request.query_params.get('error_type'):
            qs = qs.filter(error_type=error_type)
        if resolved := self.request.query_params.get('resolved'):
            qs = qs.filter(resolved=resolved == 'true')
        return qs


class SnmpThresholdRuleViewSet(viewsets.ModelViewSet):
    queryset = SnmpThresholdRule.objects.select_related('oid')
    serializer_class = SnmpThresholdRuleSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated(), IsOperator()]
        return [IsAuthenticated(), IsSupervisor()]

    @action(detail=True, methods=['post'], url_path='toggle')
    def toggle(self, request, pk=None):
        rule = self.get_object()
        rule.is_active = not rule.is_active
        rule.save(update_fields=['is_active'])
        return success_response({'is_active': rule.is_active}, "Statut modifié")


class SnmpAlertViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SnmpAlert.objects.select_related('rule', 'olt', 'metric', 'acknowledged_by')
    serializer_class = SnmpAlertSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering = ['-first_seen']

    def get_queryset(self):
        qs = super().get_queryset()
        if olt_id := self.request.query_params.get('olt'):
            qs = qs.filter(olt_id=olt_id)
        if status := self.request.query_params.get('status'):
            qs = qs.filter(status=status)
        if severity := self.request.query_params.get('severity'):
            qs = qs.filter(severity=severity)
        return qs

    @action(detail=True, methods=['post'], url_path='acknowledge')
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        if alert.status != 'active':
            return error_response("Seules les alertes actives peuvent être acquittées.", status_code=400)
        alert.status = 'acknowledged'
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        return success_response(SnmpAlertSerializer(alert).data, "Alerte acquittée")