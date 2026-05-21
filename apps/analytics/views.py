import os
from datetime import timedelta

from django.db.models import Avg, Sum, Count, Q
from django.http import FileResponse
from django.utils import timezone
from django.core.cache import cache

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin, IsSupervisor, IsOperator
from apps.core.responses import success_response, error_response

from .models import (
    KPIHistory, Report, DashboardWidget,
    NetworkDevice, TopologyLink, SSHMetricsSnapshot, NetworkTraffic,
)
from .serializers import (
    KPIHistorySerializer, ReportSerializer, DashboardWidgetSerializer,
    NetworkDeviceSerializer, TopologyLinkSerializer,
    SSHMetricsSnapshotSerializer, NetworkTrafficSerializer,
)
from .filters import (
    KPIHistoryFilter, ReportFilter, NetworkDeviceFilter, TopologyLinkFilter,
    SSHMetricsSnapshotFilter, NetworkTrafficFilter,
)


# ============================================================================
# KPI
# ============================================================================

class KPIViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = KPIHistory.objects.select_related('olt')
    serializer_class = KPIHistorySerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = KPIHistoryFilter
    ordering = ['-timestamp']

    @extend_schema(summary="KPIs calculés live depuis la base")
    @action(detail=False, methods=['get'], url_path='current')
    def current(self, request):
        cache_key = "analytics:kpi:current"
        data = cache.get(cache_key)
        if not data:
            from apps.equipements.models import OLT, ONT
            from apps.snmp_collector.models import MetricHistory, SnmpOID, PollJob
            from apps.bfd_monitor.models import BFDSession
            from apps.alerting.models import Alert
            from apps.ai_engine.models import AnomalyDetection

            now      = timezone.now()
            since_24h = now - timedelta(hours=24)

            total_olts  = OLT.objects.count()
            active_olts = OLT.objects.filter(status='active').count()
            total_onts  = ONT.objects.count()
            online_onts = ONT.objects.filter(status='online').count()

            cpu_oid = SnmpOID.objects.filter(name='cpu_usage').first()
            avg_cpu = (
                MetricHistory.objects
                .filter(oid=cpu_oid, timestamp__gte=since_24h)
                .aggregate(v=Avg('numeric_value'))['v']
                if cpu_oid else None
            )
            mem_oid = SnmpOID.objects.filter(name='memory_usage').first()
            avg_mem = (
                MetricHistory.objects
                .filter(oid=mem_oid, timestamp__gte=since_24h)
                .aggregate(v=Avg('numeric_value'))['v']
                if mem_oid else None
            )

            total_jobs   = PollJob.objects.filter(created_at__gte=since_24h).count()
            success_jobs = PollJob.objects.filter(created_at__gte=since_24h, state='success').count()
            snmp_rate    = round(success_jobs / total_jobs * 100, 1) if total_jobs else 100.0

            bfd_total = BFDSession.objects.filter(is_monitored=True).count()
            bfd_up    = BFDSession.objects.filter(is_monitored=True, state='up').count()

            alert_count   = Alert.objects.filter(status='active').count()
            anomaly_count = AnomalyDetection.objects.filter(
                resolved=False, detected_at__gte=since_24h
            ).count()

            data = {
                'total_olts':         total_olts,
                'active_olts':        active_olts,
                'total_onts':         total_onts,
                'online_onts':        online_onts,
                'avg_cpu_usage':      round(avg_cpu, 1) if avg_cpu is not None else None,
                'avg_memory_usage':   round(avg_mem, 1) if avg_mem is not None else None,
                'snmp_success_rate':  snmp_rate,
                'bfd_up_sessions':    bfd_up,
                'bfd_total_sessions': bfd_total,
                'alert_count':        alert_count,
                'anomaly_count':      anomaly_count,
            }
            cache.set(cache_key, data, 300)
        return Response(data)

    @extend_schema(summary="Tendance sur N jours — [{timestamp, value}]")
    @action(detail=False, methods=['get'], url_path='trend')
    def trend(self, request):
        days   = int(request.query_params.get('days', 7))
        metric = request.query_params.get('metric', 'online_onts')
        since  = timezone.now() - timedelta(days=days)
        qs = (
            KPIHistory.objects
            .filter(period='day', timestamp__gte=since, olt__isnull=True)
            .order_by('timestamp')
        )
        data = [
            {'timestamp': k.timestamp.isoformat(), 'value': getattr(k, metric, None)}
            for k in qs
        ]
        return Response(data)

    @extend_schema(summary="Forcer l'agrégation manuelle des KPIs")
    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated, IsSupervisor],
            url_path='force-aggregate')
    def force_aggregate(self, request):
        from .tasks import aggregate_kpi
        period = request.data.get('period', 'hour')
        aggregate_kpi.delay(period)
        return success_response(None, f"Agrégation {period} déclenchée")


# ============================================================================
# REPORT
# ============================================================================

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.select_related('generated_by').order_by('-created_at')
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ReportFilter
    search_fields = ['name']
    ordering_fields = ['created_at', 'name', 'status', 'report_type']

    def get_permissions(self):
        if self.action in ['destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated(), IsSupervisor()]

    def perform_create(self, serializer):
        from .tasks import generate_report
        report = serializer.save(generated_by=self.request.user, status='pending')
        generate_report.delay(str(report.id))

    @extend_schema(summary="Télécharger le fichier généré (PDF ou Excel)")
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        report = self.get_object()

        if report.status != 'ready':
            return error_response(
                f"Rapport non disponible (statut : {report.status})",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if not report.file or not report.file.name:
            return error_response(
                "Aucun fichier associé à ce rapport.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        try:
            file_handle = report.file.open('rb')
        except FileNotFoundError:
            return error_response(
                "Le fichier n'existe plus sur le serveur.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        filename = os.path.basename(report.file.name)
        content_type = (
            'application/pdf'
            if report.format == 'pdf'
            else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        return FileResponse(
            file_handle,
            as_attachment=True,
            filename=filename,
            content_type=content_type,
        )

    @extend_schema(summary="Relancer la génération d'un rapport")
    @action(detail=True, methods=['post'], url_path='regenerate')
    def regenerate(self, request, pk=None):
        from .tasks import generate_report
        report = self.get_object()
        if report.status == 'generating':
            return error_response(
                "Génération déjà en cours.",
                status_code=status.HTTP_409_CONFLICT,
            )
        report.status = 'pending'
        report.error_message = ''
        report.save(update_fields=['status', 'error_message'])
        generate_report.delay(str(report.id))
        return success_response(
            ReportSerializer(report, context={'request': request}).data,
            "Génération relancée.",
        )

    @extend_schema(summary="Statut de génération d'un rapport")
    @action(detail=True, methods=['get'], url_path='generation-status')
    def generation_status(self, request, pk=None):
        report = self.get_object()
        return success_response({
            'id':           str(report.id),
            'status':       report.status,
            'generated_at': report.generated_at.isoformat() if report.generated_at else None,
            'error_message': report.error_message or None,
            'file_available': bool(report.file and report.file.name),
        })


# ============================================================================
# DASHBOARD WIDGET
# ============================================================================

class DashboardWidgetViewSet(viewsets.ModelViewSet):
    serializer_class = DashboardWidgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DashboardWidget.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='reorder')
    def reorder(self, request):
        widget_ids = request.data.get('widget_ids', [])
        for idx, wid in enumerate(widget_ids):
            DashboardWidget.objects.filter(id=wid, user=request.user).update(order=idx)
        return success_response(None, "Ordre mis à jour")


# ============================================================================
# NETWORK DEVICE
# ============================================================================

class NetworkDeviceViewSet(viewsets.ModelViewSet):
    queryset = NetworkDevice.objects.select_related('site')
    serializer_class = NetworkDeviceSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = NetworkDeviceFilter
    search_fields = ['name', 'hostname', 'ip_address']
    ordering = ['site', 'name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'test_connection']:
            return [IsAuthenticated(), IsSupervisor()]
        return [IsAuthenticated(), IsOperator()]

    @extend_schema(summary="Tester la connexion SSH à un appareil")
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        from .tasks import test_device_connection
        device = self.get_object()
        test_device_connection.delay(str(device.id))
        return success_response(None, "Test de connexion lancé")

    @extend_schema(summary="Collecter les métriques SSH d'un appareil")
    @action(detail=True, methods=['post'])
    def collect_metrics(self, request, pk=None):
        from .tasks import collect_ssh_metrics
        device = self.get_object()
        collect_ssh_metrics.delay(str(device.id))
        return success_response(None, "Collecte de métriques lancée")

    @extend_schema(summary="Dernières métriques SSH")
    @action(detail=True, methods=['get'])
    def latest_metrics(self, request, pk=None):
        device = self.get_object()
        latest = SSHMetricsSnapshot.objects.filter(device=device).order_by('-timestamp').first()
        if not latest:
            return error_response("Aucune métrique disponible", status_code=404)
        return success_response(SSHMetricsSnapshotSerializer(latest).data)


# ============================================================================
# TOPOLOGY LINK
# ============================================================================

class TopologyLinkViewSet(viewsets.ModelViewSet):
    queryset = TopologyLink.objects.select_related('source_device', 'destination_device')
    serializer_class = TopologyLinkSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TopologyLinkFilter
    search_fields = ['source_device__name', 'destination_device__name']
    ordering = ['source_device', 'destination_device']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsSupervisor()]
        return [IsAuthenticated(), IsOperator()]


# ============================================================================
# SSH METRICS SNAPSHOT
# ============================================================================

class SSHMetricsSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SSHMetricsSnapshot.objects.select_related('device')
    serializer_class = SSHMetricsSnapshotSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = SSHMetricsSnapshotFilter
    ordering = ['-timestamp']

    @extend_schema(summary="Snapshots contenant des anomalies")
    @action(detail=False, methods=['get'], url_path='anomalies')
    def anomalies(self, request):
        hours = int(request.query_params.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)
        qs = (
            SSHMetricsSnapshot.objects
            .filter(is_anomaly=True, timestamp__gte=since)
            .select_related('device')
            .order_by('-timestamp')[:100]
        )
        return success_response(
            SSHMetricsSnapshotSerializer(qs, many=True).data,
            f"Anomalies détectées dans les {hours}h",
        )

    @extend_schema(summary="Statistiques CPU/Mémoire agrégées")
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        hours = int(request.query_params.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)
        stats = SSHMetricsSnapshot.objects.filter(timestamp__gte=since).aggregate(
            avg_cpu=Avg('cpu_usage_pct'),
            max_cpu=Avg('cpu_usage_pct'),
            avg_memory=Avg('memory_usage_pct'),
            avg_temperature=Avg('temperature_c'),
        )
        return success_response(stats, "Statistiques moyennes")


# ============================================================================
# NETWORK TRAFFIC
# ============================================================================

class NetworkTrafficViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NetworkTraffic.objects.select_related('interface', 'fiber_link')
    serializer_class = NetworkTrafficSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = NetworkTrafficFilter
    ordering = ['-timestamp']

    @extend_schema(summary="Interfaces actuellement congéstionnées")
    @action(detail=False, methods=['get'], url_path='congested')
    def congested(self, request):
        hours = int(request.query_params.get('hours', 1))
        since = timezone.now() - timedelta(hours=hours)
        qs = (
            NetworkTraffic.objects
            .filter(is_congested=True, timestamp__gte=since)
            .select_related('interface', 'fiber_link')
            .order_by('-timestamp')[:50]
        )
        return success_response(
            NetworkTrafficSerializer(qs, many=True).data,
            "Interfaces congéstionnées",
        )

    @extend_schema(summary="Top 10 interfaces par débit")
    @action(detail=False, methods=['get'], url_path='top-throughput')
    def top_throughput(self, request):
        hours = int(request.query_params.get('hours', 1))
        since = timezone.now() - timedelta(hours=hours)
        qs = (
            NetworkTraffic.objects
            .filter(timestamp__gte=since)
            .order_by('-throughput_mbps')[:10]
        )
        return success_response(
            NetworkTrafficSerializer(qs, many=True).data,
            "Top 10 meilleur débit",
        )
