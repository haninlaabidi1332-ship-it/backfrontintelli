from datetime import timedelta
from django.db.models import Count, Avg
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.pagination import StandardPagination
from apps.core.permissions import IsAdmin, IsSupervisor, IsOperator, CanViewAnomaly, CanManageMLModel
from apps.core.responses import success_response, error_response

from .models import MLModel, AnomalyDetection, Prediction, TrainingJob, InferenceLog
from .serializers import (
    MLModelSerializer, AnomalyDetectionSerializer, PredictionSerializer,
    TrainingJobSerializer, InferenceLogSerializer
)
from .filters import AnomalyDetectionFilter
from .tasks import train_model, detect_anomalies_for_olt, predict_metric, call_llm


class MLModelViewSet(viewsets.ModelViewSet):
    queryset = MLModel.objects.all()
    serializer_class = MLModelSerializer
    permission_classes = [IsAuthenticated, CanManageMLModel]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'], url_path='train')
    def train(self, request, pk=None):
        model = self.get_object()
        data_start = request.data.get('data_start')
        data_end = request.data.get('data_end')
        if not data_start or not data_end:
            return error_response("data_start et data_end sont requis", status_code=400)
        train_model.delay(model.id, data_start, data_end)
        return success_response(None, f"Entraînement du modèle {model.name} déclenché")

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        model = self.get_object()
        # Désactiver les autres modèles du même type si nécessaire
        MLModel.objects.filter(model_type=model.model_type, is_active=True).update(is_active=False)
        model.is_active = True
        model.save()
        return success_response({'is_active': True}, f"Modèle {model.name} activé")

    @action(detail=False, methods=['get'], url_path='active')
    def active_model(self, request):
        model_type = request.query_params.get('type')
        if model_type:
            model = MLModel.objects.filter(model_type=model_type, is_active=True).first()
        else:
            model = MLModel.objects.filter(is_active=True).first()
        if model:
            serializer = MLModelSerializer(model)
            return success_response(serializer.data, "Modèle actif récupéré")
        return error_response("Aucun modèle actif trouvé", status_code=404)


class AnomalyDetectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AnomalyDetection.objects.select_related('olt', 'ont', 'interface', 'oid', 'model')
    serializer_class = AnomalyDetectionSerializer
    permission_classes = [IsAuthenticated, CanViewAnomaly]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = AnomalyDetectionFilter
    ordering = ['-detected_at']

    @action(detail=False, methods=['post'], url_path='run')
    def run_detection(self, request):
        olt_id = request.data.get('olt')
        if not olt_id:
            return error_response("Paramètre 'olt' requis", status_code=400)
        detect_anomalies_for_olt.delay(olt_id)
        return success_response(None, f"Détection d'anomalies déclenchée pour l'OLT {olt_id}")

    @action(detail=True, methods=['post'], url_path='resolve')
    def resolve(self, request, pk=None):
        anomaly = self.get_object()
        anomaly.resolved = True
        anomaly.resolved_at = timezone.now()
        anomaly.save()
        return success_response(None, "Anomalie marquée comme résolue")


class PredictionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Prediction.objects.select_related('olt', 'ont', 'model')
    serializer_class = PredictionSerializer
    permission_classes = [IsAuthenticated, IsOperator]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['olt', 'metric_name']
    ordering = ['-prediction_time']

    @action(detail=False, methods=['post'], url_path='forecast')
    def forecast(self, request):
        olt_id = request.data.get('olt')
        metric_name = request.data.get('metric_name')
        horizon_hours = int(request.data.get('horizon_hours', 24))
        if not olt_id or not metric_name:
            return error_response("olt et metric_name requis", status_code=400)
        predict_metric.delay(olt_id, metric_name, horizon_hours)
        return success_response(None, f"Prédiction déclenchée pour {metric_name}")


class TrainingJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrainingJob.objects.select_related('model')
    serializer_class = TrainingJobSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination
    ordering = ['-started_at']


class InferenceLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InferenceLog.objects.select_related('model')
    serializer_class = InferenceLogSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]
    pagination_class = StandardPagination
    ordering = ['-timestamp']


SYSTEM_PROMPT = """You are IntelliOLT AI, the artificial intelligence assistant integrated into the IntelliOLT platform — a FTTH/GPON network monitoring system built for telecom operators.

## Your role
You help network engineers and operators to:
- Diagnose faults and anomalies on OLT equipment
- Analyze SNMP metrics (CPU, memory, traffic, interface errors, optical power)
- Interpret BFD (Bidirectional Forwarding Detection) sessions
- Understand alerts and their priority
- Suggest precise, documented corrective actions
- Anticipate problems using ML predictions (Prophet)

## IntelliOLT platform architecture
- **OLT** (Optical Line Terminal): core GPON network device, connects to clients via fiber
- **SNMP**: metrics collection protocol, polled every 60 seconds
- **BFD**: link failure detection protocol, polled every 30 seconds
- **IsolationForest**: ML model for anomaly detection on SNMP metrics
- **Prophet**: time-series forecasting model
- **Celery**: async tasks (SNMP/BFD polling, anomaly detection, report generation)
- **Alerting**: SNMP/BFD/AI rules → alerts → notifications (Email/Slack/Teams/Webhook)
- **EVE-NG**: virtual network topology simulation

## Monitored SNMP metrics
- sysUpTime, sysDescr: general OLT health
- ifInOctets, ifOutOctets: inbound/outbound traffic per interface
- ifInErrors, ifOutErrors: interface errors (fiber quality indicator)
- ifOperStatus: interface operational state (up/down)
- cpuUsage: OLT CPU load (critical threshold > 80%)
- memoryUsage: memory usage (critical threshold > 90%)
- opticalRxPower: received optical power (normal range: -8 to -27 dBm)
- opticalTxPower: transmitted optical power

## Device statuses
- **active**: operational, everything working normally
- **degraded**: degraded performance, intervention recommended
- **inactive**: offline, urgent intervention required
- **maintenance**: under planned maintenance

## Anomaly/alert severity
- **critical** (score > 0.9): imminent failure, immediate action required
- **high** (score 0.8-0.9): high risk, escalation recommended
- **medium** (score 0.6-0.8): enhanced monitoring needed
- **low** (score < 0.6): minor anomaly, keep watching

## Response rules
1. Always respond in English, with a professional and technical tone
2. Structure your response: Diagnosis → Probable cause → Impact → Recommended action
3. Quote exact metric values from the provided context
4. Suggest CLI commands or concrete actions where relevant
5. If data is insufficient, state what else should be checked
6. Use correct telecom/network terminology (GPON, PON, OLT, BFD, SNMP, dBm, etc.)
"""


def _build_live_context(olt_id=None):
    """Pull live data from DB and build a structured context string for the LLM."""
    from apps.equipements.models import OLT
    from apps.snmp_collector.models import MetricHistory
    from apps.alerting.models import Alert
    from apps.bfd_monitor.models import BFDSession
    from apps.analytics.models import KPIHistory

    now = timezone.now()
    lines = [f"=== REAL-TIME CONTEXT — {now.strftime('%d/%m/%Y %H:%M')} UTC ===\n"]

    try:
        # --- Global fleet summary ---
        total_olts = OLT.objects.count()
        active_olts = OLT.objects.filter(status='active').count()
        degraded_olts = OLT.objects.filter(status='degraded').count()
        inactive_olts = OLT.objects.filter(status='inactive').count()
        lines.append("## FLEET STATUS")
        lines.append(f"OLTs: {total_olts} total | {active_olts} active | {degraded_olts} degraded | {inactive_olts} offline\n")

        # --- OLT list ---
        olts = OLT.objects.order_by('status', 'hostname')[:20]
        if olts:
            lines.append("## OLT LIST")
            for o in olts:
                last_poll = o.last_polled_at.strftime('%H:%M:%S') if getattr(o, 'last_polled_at', None) else 'never'
                lines.append(f"  - {o.hostname} ({o.ip_address}) | status={o.status} | last poll={last_poll}")
            lines.append("")

        # --- Active alerts ---
        active_alerts = Alert.objects.filter(
            status='active'
        ).select_related('olt').order_by('-severity', '-first_seen')[:10]
        if active_alerts.exists():
            lines.append("## ACTIVE ALERTS")
            for a in active_alerts:
                olt_name = a.olt.hostname if getattr(a, 'olt', None) and a.olt else 'Global'
                lines.append(f"  [{a.severity.upper()}] {olt_name} — {a.message} (since {a.first_seen.strftime('%d/%m %H:%M')})")
            lines.append("")

        # --- Active anomalies (last 24h) ---
        recent_anomalies = AnomalyDetection.objects.filter(
            resolved=False,
            detected_at__gte=now - timedelta(hours=24)
        ).select_related('olt').order_by('-anomaly_score')[:8]
        if recent_anomalies.exists():
            lines.append("## UNRESOLVED ML ANOMALIES (24h)")
            for a in recent_anomalies:
                olt_name = a.olt.hostname if a.olt else 'Unknown'
                lines.append(
                    f"  [{a.severity.upper()}] {olt_name} | metric={a.metric_name} | "
                    f"value={a.actual_value} | score={a.anomaly_score:.2f} | "
                    f"detected={a.detected_at.strftime('%d/%m %H:%M')}"
                )
            lines.append("")

        # --- BFD sessions ---
        bfd_down = BFDSession.objects.filter(state='down').select_related('olt')[:5]
        if bfd_down.exists():
            lines.append("## BFD SESSIONS DOWN")
            for s in bfd_down:
                olt_name = s.olt.hostname if getattr(s, 'olt', None) and s.olt else 'Unknown'
                lines.append(f"  - {s.name} | OLT={olt_name} | peer={s.peer_ip} | state=DOWN")
            lines.append("")

        # --- OLT-specific deep context ---
        if olt_id:
            try:
                olt = OLT.objects.get(id=olt_id)
                lines.append(f"## FOCUS OLT: {olt.hostname}")
                lines.append(f"  IP={olt.ip_address} | status={olt.status} | model={getattr(olt, 'model', 'N/A')} | vendor={getattr(olt, 'vendor', 'N/A')}")

                # Recent metrics (last 2h)
                metrics = MetricHistory.objects.filter(
                    olt=olt,
                    timestamp__gte=now - timedelta(hours=2),
                    numeric_value__isnull=False
                ).select_related('oid').order_by('oid__name', '-timestamp').distinct('oid__name')[:15]
                if metrics:
                    lines.append("  Recent metrics (2h):")
                    for m in metrics:
                        lines.append(f"    {m.oid.name}: {m.numeric_value} {m.oid.unit or ''} (at {m.timestamp.strftime('%H:%M:%S')})")

                # OLT anomalies
                olt_anomalies = AnomalyDetection.objects.filter(
                    olt=olt, detected_at__gte=now - timedelta(hours=48)
                ).order_by('-detected_at')[:5]
                if olt_anomalies:
                    lines.append("  Anomalies (48h):")
                    for a in olt_anomalies:
                        resolved_str = "resolved" if a.resolved else "active"
                        lines.append(f"    [{resolved_str}] {a.metric_name}={a.actual_value} score={a.anomaly_score:.2f} severity={a.severity}")

                # OLT alerts
                olt_alerts = Alert.objects.filter(
                    olt=olt, status='active'
                ).order_by('-severity')[:5]
                if olt_alerts:
                    lines.append("  Active alerts:")
                    for a in olt_alerts:
                        lines.append(f"    [{a.severity.upper()}] {a.message}")

                lines.append("")
            except OLT.DoesNotExist:
                pass

    except Exception as e:
        lines.append(f"(Error retrieving context: {e})\n")

    return "\n".join(lines)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ask_ai(request):
    """
    POST /api/ai/ask/
    Body: { "question": "...", "olt_id": <uuid> (optional) }
    """
    question = request.data.get('question', '').strip()
    if not question:
        return Response({'error': "Le champ 'question' est requis."}, status=400)

    olt_id = request.data.get('olt_id')
    live_context = _build_live_context(olt_id=olt_id)

    full_prompt = f"{live_context}\n\n=== OPERATOR QUESTION ===\n{question}"
    answer = call_llm(full_prompt, SYSTEM_PROMPT)
    return Response({'question': question, 'answer': answer})
