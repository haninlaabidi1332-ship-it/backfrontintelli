import logging
import requests
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from .models import AlertRule, Alert, NotificationChannel, NotificationHistory

logger = logging.getLogger(__name__)

@shared_task(name='alerting.send_alert_notification')
def send_alert_notification(channel_id, alert_id, message_template=None):
    """Envoie une notification via un canal, avec gestion d'erreur et historique."""
    try:
        channel = NotificationChannel.objects.get(id=channel_id, is_active=True)
    except NotificationChannel.DoesNotExist:
        logger.error(f"Canal {channel_id} introuvable ou inactif")
        return

    alert = None
    if alert_id:
        try:
            alert = Alert.objects.select_related('olt').get(id=alert_id)
            # Formatter le message avec le contexte
            context = {
                'olt': alert.olt.hostname if alert.olt else 'N/A',
                'severity': alert.get_severity_display(),
                'value': alert.value,
                'message': alert.message,
                'source_id': alert.source_id,
            }
            message = alert.message
            if message_template:
                message = message_template.format(**context)
        except Alert.DoesNotExist:
            message = message_template or "Test d'alerte"
    else:
        message = message_template or "Test d'alerte"

    success = False
    response_text = ""
    try:
        if channel.channel_type == 'email':
            recipients = channel.configuration.get('recipients', [])
            if recipients:
                send_mail(
                    subject=f"[IntelliOLT] Alerte{' ' + alert.get_severity_display() if alert else ''}",
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipients,
                    fail_silently=False,
                )
                success = True
        elif channel.channel_type == 'slack':
            webhook_url = channel.configuration.get('webhook_url')
            if webhook_url:
                payload = {'text': message}
                resp = requests.post(webhook_url, json=payload, timeout=5)
                if resp.status_code == 200:
                    success = True
                response_text = resp.text
        elif channel.channel_type == 'teams':
            webhook_url = channel.configuration.get('webhook_url')
            if webhook_url:
                payload = {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "summary": "Alerte IntelliOLT",
                    "text": message
                }
                resp = requests.post(webhook_url, json=payload, timeout=5)
                if resp.status_code == 200:
                    success = True
                response_text = resp.text
        elif channel.channel_type == 'webhook':
            url = channel.configuration.get('url')
            headers = channel.configuration.get('headers', {})
            method = channel.configuration.get('method', 'POST')
            if method.upper() == 'POST':
                resp = requests.post(url, json={'message': message, 'alert_id': alert_id}, headers=headers, timeout=5)
            else:
                resp = requests.get(url, params={'message': message}, headers=headers, timeout=5)
            if resp.status_code in (200, 201, 202):
                success = True
            response_text = resp.text[:500]
    except Exception as e:
        logger.exception(f"Erreur d'envoi sur {channel.name}")
        response_text = str(e)

    if alert_id:
        NotificationHistory.objects.create(
            alert_id=alert_id,
            channel=channel,
            success=success,
            response=response_text
        )
    logger.info(f"Notification via {channel.name} : {'OK' if success else 'FAILED'}")

@shared_task(name='alerting.evaluate_rules_for_olt')
def evaluate_rules_for_olt(olt_id):
    from apps.snmp_collector.models import SnmpAlert
    from apps.bfd_monitor.models import BFDActiveAlert
    from apps.ai_engine.models import AnomalyDetection
    from .models import AlertRule, Alert
    from django.conf import settings
    from django.utils import timezone
    from datetime import timedelta

    # ── Simulation mode: fire/resolve alerts based on recent SNMP metrics ─────
    if getattr(settings, 'SIMULATION_MODE', False):
        from apps.equipements.models import OLT
        from apps.snmp_collector.models import MetricHistory
        try:
            olt = OLT.objects.get(id=olt_id)
        except OLT.DoesNotExist:
            return

        since = timezone.now() - timedelta(minutes=10)

        thresholds = [
            ('cpu_usage',    80.0, 'critical', 'CPU {value:.1f}% on {olt}, threshold exceeded'),
            ('memory_usage', 84.0, 'warning',  'Memory {value:.1f}% on {olt}, high usage'),
            ('temperature',  62.0, 'major',    'Temperature {value:.1f}C on {olt}, check cooling'),
        ]

        for oid_frag, threshold, severity, template in thresholds:
            latest = MetricHistory.objects.filter(
                olt=olt, oid__name__icontains=oid_frag,
                timestamp__gte=since, numeric_value__isnull=False
            ).order_by('-timestamp').first()

            active_alert = Alert.objects.filter(
                olt=olt, status='active', message__icontains=oid_frag.replace('_', ' ')
            ).first()

            if latest and latest.numeric_value > threshold:
                if not active_alert:
                    Alert.objects.create(
                        olt=olt,
                        severity=severity,
                        status='active',
                        message=template.format(value=latest.numeric_value, olt=olt.hostname),
                        value=latest.numeric_value,
                    )
                    logger.info("[SIM] Alert fired: %s=%.1f on %s", oid_frag, latest.numeric_value, olt.hostname)
            elif active_alert:
                active_alert.status = 'resolved'
                active_alert.cleared_at = timezone.now()
                active_alert.save(update_fields=['status', 'cleared_at'])
                logger.info("[SIM] Alert resolved: %s on %s", oid_frag, olt.hostname)
        return

    rules = AlertRule.objects.filter(is_active=True)
    for rule in rules:
        if rule.source_type == 'snmp' and rule.snmp_rule:
            snmp_alerts = SnmpAlert.objects.filter(
                rule=rule.snmp_rule, olt_id=olt_id, status='active'
            )
            for sa in snmp_alerts:
                # Déduplication
                exists = Alert.objects.filter(
                    rule=rule, olt_id=olt_id, source_id=str(sa.id)
                ).exists()
                if exists:
                    continue
                alert = Alert.objects.create(
                    rule=rule,
                    olt_id=olt_id,
                    source_id=str(sa.id),
                    severity=sa.severity.upper(),
                    message=rule.message_template.format(
                        olt=sa.olt.hostname, value=sa.value, severity=sa.severity, source='SNMP'
                    ),
                    value=sa.value
                )
                # Notifications
                for channel in NotificationChannel.objects.filter(is_active=True):
                    send_alert_notification.delay(channel.id, alert.id, None)
        elif rule.source_type == 'bfd' and rule.bfd_rule:
            bfd_alerts = BFDActiveAlert.objects.filter(
                rule=rule.bfd_rule, session__olt_id=olt_id, status='active'
            )
            for ba in bfd_alerts:
                exists = Alert.objects.filter(
                    rule=rule, olt_id=olt_id, source_id=str(ba.id)
                ).exists()
                if exists:
                    continue
                alert = Alert.objects.create(
                    rule=rule,
                    olt_id=olt_id,
                    source_id=str(ba.id),
                    severity=ba.severity.upper(),
                    message=rule.message_template.format(
                        session=ba.session.name, value=ba.value, severity=ba.severity, source='BFD'
                    ),
                    value=ba.value
                )
                for channel in NotificationChannel.objects.filter(is_active=True):
                    send_alert_notification.delay(channel.id, alert.id, None)
        elif rule.source_type == 'ai' and rule.ai_severity_min:
            anomalies = AnomalyDetection.objects.filter(
                olt_id=olt_id,
                resolved=False,
                severity__gte=rule.ai_severity_min
            )
            for anom in anomalies:
                exists = Alert.objects.filter(
                    rule=rule, olt_id=olt_id, source_id=str(anom.id)
                ).exists()
                if exists:
                    continue
                alert = Alert.objects.create(
                    rule=rule,
                    olt_id=olt_id,
                    source_id=str(anom.id),
                    severity=anom.severity.upper(),
                    message=rule.message_template.format(
                        olt=anom.olt.hostname, metric=anom.metric_name, value=anom.actual_value, severity=anom.severity, source='AI'
                    ),
                    value=anom.anomaly_score
                )
                for channel in NotificationChannel.objects.filter(is_active=True):
                    send_alert_notification.delay(channel.id, alert.id, None)

    # Auto-resolve active alerts whose underlying source is no longer active
    _auto_resolve_stale_alerts(olt_id)


def _auto_resolve_stale_alerts(olt_id):
    """Resolve alerts whose source (SNMP/BFD/AI) is no longer active."""
    from apps.snmp_collector.models import SnmpAlert
    from apps.bfd_monitor.models import BFDActiveAlert
    from apps.ai_engine.models import AnomalyDetection
    from .models import Alert
    from django.utils import timezone

    active_alerts = Alert.objects.filter(olt_id=olt_id, status='active').select_related('rule')
    for alert in active_alerts:
        if not alert.rule or not alert.source_id:
            continue
        rule = alert.rule
        still_active = True
        try:
            if rule.source_type == 'snmp':
                still_active = SnmpAlert.objects.filter(id=alert.source_id, status='active').exists()
            elif rule.source_type == 'bfd':
                still_active = BFDActiveAlert.objects.filter(id=alert.source_id, status='active').exists()
            elif rule.source_type == 'ai':
                still_active = AnomalyDetection.objects.filter(id=alert.source_id, resolved=False).exists()
        except Exception:
            continue
        if not still_active:
            alert.status = 'resolved'
            alert.cleared_at = timezone.now()
            alert.save(update_fields=['status', 'cleared_at'])


@shared_task(name='alerting.evaluate_all_rules')
def evaluate_all_rules():
    """Evaluate alert rules for every active OLT."""
    from apps.equipements.models import OLT
    olt_ids = list(OLT.objects.filter(status__in=['active', 'degraded']).values_list('id', flat=True))
    for olt_id in olt_ids:
        evaluate_rules_for_olt.delay(olt_id)
    logger.info("evaluate_all_rules: %d OLTs scheduled", len(olt_ids))
    return {"scheduled": len(olt_ids)}