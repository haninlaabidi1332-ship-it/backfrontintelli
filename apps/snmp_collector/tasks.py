import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)

# --- Helper SNMP ----------------------------------------------------
def _snmp_imports():
    from pysnmp.hlapi import (
        SnmpEngine, CommunityData, UsmUserData,
        UdpTransportTarget, ContextData,
        ObjectType, ObjectIdentity, getCmd,
        usmHMACMD5AuthProtocol, usmHMACSHAAuthProtocol,
        usmDESPrivProtocol, usmAesCfb128Protocol,
    )
    return (SnmpEngine, CommunityData, UsmUserData, UdpTransportTarget,
            ContextData, ObjectType, ObjectIdentity, getCmd,
            usmHMACMD5AuthProtocol, usmHMACSHAAuthProtocol,
            usmDESPrivProtocol, usmAesCfb128Protocol)


def _build_community_data(olt):
    """Construit les données d'authentification SNMP selon la version."""
    _, CommunityData, UsmUserData, *_, \
        usmHMACMD5AuthProtocol, usmHMACSHAAuthProtocol, \
        usmDESPrivProtocol, usmAesCfb128Protocol = _snmp_imports()

    if olt.snmp_version == '3':
        auth_proto = usmHMACSHAAuthProtocol if olt.snmp_v3_auth_protocol == 'SHA' else usmHMACMD5AuthProtocol
        priv_proto = usmAesCfb128Protocol if olt.snmp_v3_priv_protocol == 'AES' else usmDESPrivProtocol
        return UsmUserData(
            userName=olt.snmp_v3_username,
            authKey=olt.snmp_v3_auth_key,
            privKey=olt.snmp_v3_priv_key,
            authProtocol=auth_proto,
            privProtocol=priv_proto,
        )
    mp_model = 0 if olt.snmp_version == '1' else 1
    return CommunityData(olt.snmp_community, mpModel=mp_model)


def fetch_snmp_value(olt, oid_str: str, timeout: float = 2.0, retries: int = 2):
    """Retourne (raw_value, numeric_value, error)."""
    (SnmpEngine, _, _, UdpTransportTarget, ContextData,
     ObjectType, ObjectIdentity, getCmd, *_) = _snmp_imports()

    try:
        auth_data = _build_community_data(olt)
        transport = UdpTransportTarget((olt.ip_address, olt.snmp_port),
                                       timeout=timeout, retries=retries)
        iterator = getCmd(SnmpEngine(), auth_data, transport,
                          ContextData(), ObjectType(ObjectIdentity(oid_str)))
        err_ind, err_status, err_idx, var_binds = next(iterator)

        if err_ind:
            return None, None, f"indication={err_ind}"
        if err_status:
            return None, None, f"status={err_status.prettyPrint()}"
        if not var_binds:
            return None, None, "empty response"

        raw = str(var_binds[0][1])
        try:
            numeric = float(int(var_binds[0][1]))
        except Exception:
            try:
                numeric = float(raw)
            except Exception:
                numeric = None
        return raw, numeric, None
    except Exception as exc:
        return None, None, str(exc)


# --- Tâches Celery -------------------------------------------------
@shared_task(bind=True, max_retries=2, default_retry_delay=30, name='snmp.poll_single_olt')
def poll_single_olt(self, olt_id: str):
    """Collecte toutes les métriques d'un OLT."""
    from apps.equipements.models import OLT
    from .models import SnmpOID, MetricHistory, PollJob, SnmpErrorLog, SnmpThresholdRule, SnmpAlert

    lock_key = f"snmp_poll_lock:{olt_id}"
    if not cache.add(lock_key, '1', timeout=90):
        logger.info("poll_single_olt: OLT %s déjà en cours, ignoré.", olt_id)
        return {"skipped": True, "reason": "locked"}

    try:
        olt = OLT.objects.select_related('vendor').get(id=olt_id)
    except OLT.DoesNotExist:
        cache.delete(lock_key)
        logger.error("poll_single_olt: OLT %s introuvable.", olt_id)
        return

    if olt.status not in ('active', 'degraded'):
        cache.delete(lock_key)
        logger.info("poll_single_olt: OLT %s inactif, ignoré.", olt.hostname)
        return

    oids = SnmpOID.objects.filter(is_active=True)
    job = PollJob.objects.create(olt=olt, state=PollJob.State.RUNNING, started_at=timezone.now())
    metrics_batch = []
    collected = 0
    failed = 0

    for oid_obj in oids:
        raw, numeric, error = fetch_snmp_value(olt, oid_obj.oid)
        if error:
            failed += 1
            SnmpErrorLog.objects.create(
                olt=olt, oid=oid_obj,
                error_type="timeout" if "timeout" in error.lower() else "other",
                error_message=error,
            )
            logger.warning("SNMP %s [%s] : %s", olt.hostname, oid_obj.name, error)
        else:
            scaled = numeric * oid_obj.scale_factor if numeric is not None else None
            metrics_batch.append(MetricHistory(
                olt=olt, oid=oid_obj,
                raw_value=raw or '',
                numeric_value=scaled,
            ))
            collected += 1

        if len(metrics_batch) >= 500:
            MetricHistory.objects.bulk_create(metrics_batch, batch_size=500)
            metrics_batch = []

    if metrics_batch:
        MetricHistory.objects.bulk_create(metrics_batch, batch_size=500)

    now = timezone.now()
    job.state = PollJob.State.SUCCESS if failed == 0 else PollJob.State.PARTIAL
    job.finished_at = now
    job.metrics_collected = collected
    job.metrics_failed = failed
    job.save()

    olt.last_polled_at = now
    olt.save(update_fields=["last_polled_at"])

    # Évaluation des seuils SNMP
    evaluate_snmp_thresholds.delay(olt_id)

    cache.delete(lock_key)
    logger.info("poll_single_olt: %s — %d ok, %d erreurs.", olt.hostname, collected, failed)
    return {"olt": olt.hostname, "collected": collected, "failed": failed}


@shared_task(name='snmp.collect_all_olts')
def collect_all_metrics():
    """Lance la collecte pour tous les OLTs actifs."""
    from apps.equipements.models import OLT
    olt_ids = list(OLT.objects.filter(
        status__in=['active', 'degraded'], deleted_at__isnull=True
    ).values_list('id', flat=True))
    for olt_id in olt_ids:
        poll_single_olt.delay(str(olt_id))
    logger.info("collect_all_metrics: %d OLTs planifiés.", len(olt_ids))
    return {"scheduled": len(olt_ids)}


@shared_task(name='snmp.purge_old_metrics')
def purge_old_metrics(days: int = 90):
    from .models import MetricHistory
    cutoff = timezone.now() - timedelta(days=days)
    deleted, _ = MetricHistory.objects.filter(timestamp__lt=cutoff).delete()
    logger.info("purge_old_metrics: %d enregistrements supprimés (> %d jours).", deleted, days)
    return {"deleted": deleted}


@shared_task(name='snmp.evaluate_snmp_thresholds')
def evaluate_snmp_thresholds(olt_id: str):
    from .models import SnmpThresholdRule, SnmpAlert, SnmpOID, MetricHistory
    from apps.equipements.models import OLT
    try:
        olt = OLT.objects.get(id=olt_id)
    except OLT.DoesNotExist:
        return

    # Récupérer la dernière métrique par OID
    latest_metrics = {}
    for metric in MetricHistory.objects.filter(olt=olt, numeric_value__isnull=False).order_by('-timestamp'):
        if metric.oid_id not in latest_metrics:
            latest_metrics[metric.oid_id] = metric.numeric_value

    rules = SnmpThresholdRule.objects.filter(is_active=True)
    for rule in rules:
        value = latest_metrics.get(rule.oid_id)
        if value is None:
            continue

        ops = {
            '>': value > rule.threshold,
            '<': value < rule.threshold,
            '>=': value >= rule.threshold,
            '<=': value <= rule.threshold,
            '=': value == rule.threshold,
            '!=': value != rule.threshold,
        }
        triggered = ops.get(rule.operator, False)

        if triggered:
            cooldown_key = f"snmp_alert_cooldown:{rule.id}:{olt.id}"
            if cache.get(cooldown_key):
                continue
            SnmpAlert.objects.get_or_create(
                rule=rule, olt=olt, status='active',
                defaults={
                    'value': value,
                    'severity': rule.severity,
                    'message': rule.message.format(value=value, threshold=rule.threshold, olt=olt.hostname),
                }
            )
            cache.set(cooldown_key, '1', timeout=rule.cooldown_minutes * 60)
        else:
            SnmpAlert.objects.filter(rule=rule, olt=olt, status='active').update(
                status='resolved', cleared_at=timezone.now()
            )