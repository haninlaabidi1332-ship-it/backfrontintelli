import logging
from datetime import timedelta
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Avg, Count, Q
from .models import KPIHistory, Report
from apps.equipements.models import OLT, ONT
from apps.snmp_collector.models import MetricHistory, SnmpOID, PollJob
from apps.bfd_monitor.models import BFDSession
from apps.ai_engine.models import AnomalyDetection
from apps.alerting.models import Alert
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import openpyxl
from openpyxl.drawing.image import Image as XLImage
import os

logger = logging.getLogger(__name__)

@shared_task(name='analytics.aggregate_kpi')
def aggregate_kpi(period='hour'):
    """Agrégation des KPIs pour la période donnée."""
    now = timezone.now()
    if period == 'hour':
        start = now - timedelta(hours=1)
    elif period == 'day':
        start = now - timedelta(days=1)
    elif period == 'week':
        start = now - timedelta(weeks=1)
    elif period == 'month':
        start = now - timedelta(days=30)
    else:
        return

    total_olts = OLT.objects.count()
    active_olts = OLT.objects.filter(status='active').count()
    total_onts = ONT.objects.count()
    online_onts = ONT.objects.filter(status='online').count()

    cpu_oid = SnmpOID.objects.filter(name__icontains='cpu').first()
    avg_cpu = None
    if cpu_oid:
        avg_cpu = MetricHistory.objects.filter(oid=cpu_oid, timestamp__gte=start).aggregate(Avg('numeric_value'))['numeric_value__avg']

    mem_oid = SnmpOID.objects.filter(name__icontains='memory').first()
    avg_mem = None
    if mem_oid:
        avg_mem = MetricHistory.objects.filter(oid=mem_oid, timestamp__gte=start).aggregate(Avg('numeric_value'))['numeric_value__avg']

    temp_oid = SnmpOID.objects.filter(name__icontains='temperature').first()
    avg_temp = None
    if temp_oid:
        avg_temp = MetricHistory.objects.filter(oid=temp_oid, timestamp__gte=start).aggregate(Avg('numeric_value'))['numeric_value__avg']

    rx_oid = SnmpOID.objects.filter(name__icontains='rx_power').first()
    avg_rx = None
    if rx_oid:
        avg_rx = MetricHistory.objects.filter(oid=rx_oid, timestamp__gte=start).aggregate(Avg('numeric_value'))['numeric_value__avg']

    total_jobs = PollJob.objects.filter(created_at__gte=start).count()
    success_jobs = PollJob.objects.filter(created_at__gte=start, state='success').count()
    snmp_success = (success_jobs / total_jobs * 100) if total_jobs else 100.0

    bfd_total = BFDSession.objects.filter(is_monitored=True).count()
    bfd_up = BFDSession.objects.filter(is_monitored=True, state='up').count()

    anomaly_count = AnomalyDetection.objects.filter(detected_at__gte=start).count()
    alert_count = Alert.objects.filter(first_seen__gte=start).count()

    KPIHistory.objects.create(
        period=period,
        timestamp=now,
        total_olts=total_olts,
        active_olts=active_olts,
        total_onts=total_onts,
        online_onts=online_onts,
        avg_cpu_usage=avg_cpu,
        avg_memory_usage=avg_mem,
        avg_temperature=avg_temp,
        avg_rx_power=avg_rx,
        snmp_success_rate=snmp_success,
        bfd_total_sessions=bfd_total,
        bfd_up_sessions=bfd_up,
        anomaly_count=anomaly_count,
        alert_count=alert_count
    )
    # Invalider cache
    cache.delete("analytics:kpi:current")
    logger.info(f"KPIs agrégés ({period})")

@shared_task(name='analytics.generate_report')
def generate_report(report_id):
    from django.core.files.base import ContentFile
    try:
        report = Report.objects.get(id=report_id)
    except Report.DoesNotExist:
        return
    report.status = 'generating'
    report.save()

    try:
        # Récupérer données
        kpis = KPIHistory.objects.filter(
            period='day',
            timestamp__range=(report.date_from, report.date_to)
        ).order_by('timestamp')
        if not kpis.exists():
            raise ValueError("Pas de données pour la période")

        # Création du rapport selon format
        if report.format == 'pdf':
            buffer = generate_pdf_report(kpis, report)
            ext = 'pdf'
            content_type = 'application/pdf'
        else:
            buffer = generate_excel_report(kpis, report)
            ext = 'xlsx'
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        filename = f"report_{report.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
        report.file.save(filename, ContentFile(buffer.getvalue()))
        report.status = 'ready'
        report.generated_at = timezone.now()
        report.save()
        logger.info(f"Rapport {report.name} généré avec succès")
    except Exception as e:
        report.status = 'failed'
        report.error_message = str(e)
        report.save()
        logger.exception(f"Erreur génération rapport {report.name}")

def generate_pdf_report(kpis, report):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    title = f"Rapport {report.get_report_type_display()} - {report.date_from.strftime('%d/%m/%Y')} au {report.date_to.strftime('%d/%m/%Y')}"
    story.append(Paragraph(title, styles['Title']))
    story.append(Spacer(1, 12))

    # Tableau des KPIs
    data = [['Date', 'OLTs actifs', 'ONT en ligne', 'CPU moy.', 'Anomalies', 'Alertes']]
    for k in kpis:
        data.append([
            k.timestamp.strftime('%d/%m/%Y'),
            k.active_olts,
            k.online_onts,
            f"{k.avg_cpu_usage:.1f}%" if k.avg_cpu_usage else '-',
            k.anomaly_count,
            k.alert_count
        ])
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_excel_report(kpis, report):
    buffer = BytesIO()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "KPIs"
    headers = ['Date', 'Total OLTs', 'OLTs actifs', 'Total ONTs', 'ONT en ligne', 
               'CPU moy.', 'Mémoire moy.', 'Température', 'RX Power', 'SNMP succès %',
               'BFD UP', 'Anomalies', 'Alertes']
    ws.append(headers)
    for k in kpis:
        ws.append([
            k.timestamp.strftime('%Y-%m-%d'),
            k.total_olts, k.active_olts, k.total_onts, k.online_onts,
            k.avg_cpu_usage, k.avg_memory_usage, k.avg_temperature, k.avg_rx_power,
            k.snmp_success_rate, k.bfd_up_sessions, k.anomaly_count, k.alert_count
        ])
    wb.save(buffer)
    buffer.seek(0)
    return buffer