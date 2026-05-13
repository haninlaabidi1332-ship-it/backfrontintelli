import logging
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from django.db.models import F

logger = logging.getLogger(__name__)

# --- Helper de collecte (à remplacer par vraie collecte SNMP/CLI) ---
def fetch_bfd_status(session):
    """
    Simulateur de collecte BFD.
    À remplacer par un vrai appel SNMP (pysnmp) ou CLI, en fonction de session.snmp_oid_state.
    """
    import random
    current_state = session.state
    # Simulation simple
    if current_state == 'up':
        new_state = 'up' if random.random() < 0.95 else 'down'
    else:
        new_state = 'up' if random.random() < 0.3 else current_state

    # Incréments
    up_inc = 1 if new_state == 'up' and current_state != 'up' else 0
    down_inc = 1 if new_state == 'down' and current_state != 'down' else 0
    flap_inc = 1 if (new_state != current_state and (session.up_count + session.down_count) > 0) else 0

    # Métriques simulées
    packets_sent = session.packets_sent + random.randint(10, 100)
    packets_received = session.packets_received + random.randint(0, 99)
    loss_rate = max(0, (packets_sent - packets_received) / packets_sent * 100) if packets_sent else 0

    return {
        'state': new_state,
        'up_count_inc': up_inc,
        'down_count_inc': down_inc,
        'flap_count_inc': flap_inc,
        'diagnostic': 0,
        'packets_sent': packets_sent,
        'packets_received': packets_received,
        'packets_lost': packets_sent - packets_received,
        'loss_rate_pct': loss_rate,
        'remote_state': 'up' if new_state == 'up' else 'down',
        'actual_tx_interval_ms': session.desired_tx_interval_ms,
        'actual_rx_interval_ms': session.required_rx_interval_ms,
        'uptime_seconds': session.uptime_seconds + 1 if new_state == 'up' else 0,
    }


@shared_task(name='bfd.poll_session')
def poll_bfd_session(session_id):
    from .models import BFDSession, BFDStateHistory, BFDThresholdRule, BFDActiveAlert

    lock_key = f"bfd_poll_{session_id}"
    if not cache.add(lock_key, '1', timeout=60):
        logger.info("poll_bfd_session: session %s déjà en cours.", session_id)
        return

    try:
        session = BFDSession.objects.get(id=session_id)
        if not session.is_monitored or not session.is_enabled:
            cache.delete(lock_key)
            return

        old_state = session.state
        data = fetch_bfd_status(session)

        now = timezone.now()

        # Mise à jour des compteurs
        session.up_count += data['up_count_inc']
        session.down_count += data['down_count_inc']
        session.flap_count += data['flap_count_inc']
        if data['state'] == 'up' and old_state != 'up':
            session.last_up_at = now
        elif data['state'] == 'down' and old_state != 'down':
            session.last_down_at = now
        session.state = data['state']
        session.diagnostic = data['diagnostic']
        session.remote_state = data['remote_state']
        session.packets_sent = data['packets_sent']
        session.packets_received = data['packets_received']
        session.packets_lost = data['packets_lost']
        session.loss_rate_pct = data['loss_rate_pct']
        session.actual_tx_interval_ms = data['actual_tx_interval_ms']
        session.actual_rx_interval_ms = data['actual_rx_interval_ms']
        session.uptime_seconds = data['uptime_seconds']
        if old_state != data['state']:
            session.last_state_change = now
        session.save()

        # Historique
        if old_state != data['state']:
            last_history = BFDStateHistory.objects.filter(session=session).first()
            duration_ms = None
            if last_history:
                duration_ms = int((now - last_history.timestamp).total_seconds() * 1000)
            BFDStateHistory.objects.create(
                session=session,
                previous_state=old_state,
                new_state=data['state'],
                diagnostic=data['diagnostic'],
                duration_previous_ms=duration_ms,
                triggered_alert=False
            )

        # Évaluation des seuils
        evaluate_bfd_thresholds.delay(session_id)

    except Exception as e:
        logger.exception("Erreur polling BFD session %s: %s", session_id, e)
    finally:
        cache.delete(lock_key)


@shared_task(name='bfd.poll_all_sessions')
def poll_all_bfd_sessions():
    from .models import BFDSession, BFDPollingSchedule

    sessions = BFDSession.objects.filter(is_monitored=True, is_enabled=True)
    scheduled = 0
    for session in sessions:
        olt = session.olt or (session.link.interface_a.olt if session.link else None)
        interval = 30
        if olt:
            try:
                schedule = BFDPollingSchedule.objects.get(olt=olt, is_active=True)
                interval = schedule.poll_interval_seconds
            except BFDPollingSchedule.DoesNotExist:
                pass
        # Pour une tâche périodique globale, on appelle simplement toutes les sessions
        poll_bfd_session.delay(str(session.id))
        scheduled += 1

    logger.info("poll_all_bfd_sessions: %d sessions planifiées.", scheduled)
    return {"scheduled": scheduled}


@shared_task(name='bfd.evaluate_thresholds')
def evaluate_bfd_thresholds(session_id):
    from .models import BFDSession, BFDThresholdRule, BFDActiveAlert, BFDStateHistory
    from django.core.cache import cache

    try:
        session = BFDSession.objects.get(id=session_id)
    except BFDSession.DoesNotExist:
        return

    rules = BFDThresholdRule.objects.filter(is_active=True)
    now = timezone.now()

    for rule in rules:
        triggered = False
        value = None

        if rule.metric == 'state_down':
            last_change = BFDStateHistory.objects.filter(session=session, new_state='down').first()
            if last_change and not last_change.triggered_alert:
                triggered = True
                value = 1
                last_change.triggered_alert = True
                last_change.save(update_fields=['triggered_alert'])
        elif rule.metric == 'loss_rate':
            val = session.loss_rate_pct
            if rule.operator == '>':
                triggered = val > rule.threshold
            elif rule.operator == '<':
                triggered = val < rule.threshold
            elif rule.operator == '>=':
                triggered = val >= rule.threshold
            elif rule.operator == '<=':
                triggered = val <= rule.threshold
            else:
                triggered = val == rule.threshold
            value = val
        elif rule.metric == 'detect_time':
            val = session.detect_time_ms
            if rule.operator == '>':
                triggered = val > rule.threshold
            elif rule.operator == '<':
                triggered = val < rule.threshold
            elif rule.operator == '>=':
                triggered = val >= rule.threshold
            elif rule.operator == '<=':
                triggered = val <= rule.threshold
            else:
                triggered = val == rule.threshold
            value = val
        elif rule.metric == 'flap_rate':
            val = session.flap_rate
            if rule.operator == '>':
                triggered = val > rule.threshold
            value = val
        elif rule.metric == 'availability':
            val = session.availability_pct
            if rule.operator == '<':
                triggered = val < rule.threshold
            value = val

        if triggered:
            cooldown_key = f"bfd_alert_cooldown:{rule.id}:{session.id}"
            if cache.get(cooldown_key):
                continue
            BFDActiveAlert.objects.get_or_create(
                rule=rule, session=session, status='active',
                defaults={
                    'value': value,
                    'severity': rule.severity,
                    'message': rule.message.format(
                        session=session.name, value=value, threshold=rule.threshold
                    ) if '{' in rule.message else rule.message,
                }
            )
            cache.set(cooldown_key, '1', timeout=rule.cooldown_minutes * 60)
        else:
            BFDActiveAlert.objects.filter(rule=rule, session=session, status='active').update(
                status='resolved', cleared_at=now
            )


def register_beat_schedule():
    """Enregistre la tâche périodique dans Celery Beat – appelé dans apps.py."""
    from django_celery_beat.models import PeriodicTask, IntervalSchedule
    schedule, _ = IntervalSchedule.objects.get_or_create(every=30, period=IntervalSchedule.SECONDS)
    PeriodicTask.objects.get_or_create(
        name='poll_all_bfd_sessions',
        task='bfd.poll_all_sessions',
        interval=schedule,
        defaults={'enabled': True}
    )