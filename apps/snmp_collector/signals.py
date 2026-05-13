# apps/snmp_collector/signals.py
"""
Signaux Django pour l'application snmp_collector.
- Met à jour last_polled_at de l'OLT quand une métrique est créée.
- Déclenche une notification lorsqu'une alerte SNMP apparaît.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import MetricHistory, SnmpAlert

logger = logging.getLogger(__name__)


@receiver(post_save, sender=MetricHistory)
def update_olt_last_polled(sender, instance, created, **kwargs):
    """
    Met à jour le champ last_polled_at de l'OLT parent chaque fois qu'une nouvelle métrique est créée.
    Cela permet de connaître le dernier instant où une collecte a réussi pour cet OLT.
    """
    if created and instance.olt:
        # Éviter de faire trop d'écritures : on ne met à jour que si cela fait plus de 10 secondes
        now = timezone.now()
        last = instance.olt.last_polled_at
        if not last or (now - last).total_seconds() > 10:
            instance.olt.last_polled_at = now
            instance.olt.save(update_fields=['last_polled_at'])
            logger.debug("OLT %s last_polled_at mis à jour via signal", instance.olt.hostname)


@receiver(post_save, sender=SnmpAlert)
def notify_snmp_alert(sender, instance, created, **kwargs):
    """
    Déclenche une notification (email, webhook, etc.) lorsqu'une nouvelle alerte SNMP est créée.
    À implémenter selon votre infrastructure de notifications.
    """
    if created and instance.status == 'active':
        logger.info("🔔 Nouvelle alerte SNMP : %s sur %s (valeur=%.2f)", 
                    instance.rule.name, instance.olt.hostname, instance.value)
        
        # --- Exemple d'appel à un webhook (décommentez et configurez) ---
        # import requests
        # webhook_url = "https://votre-serveur.com/webhook/snmp"
        # try:
        #     requests.post(webhook_url, json={
        #         'alert_id': str(instance.id),
        #         'rule': instance.rule.name,
        #         'olt': instance.olt.hostname,
        #         'value': instance.value,
        #         'severity': instance.severity,
        #         'message': instance.message,
        #         'timestamp': instance.first_seen.isoformat()
        #     }, timeout=2)
        # except Exception as e:
        #     logger.error("Échec d'envoi webhook pour alerte %s: %s", instance.id, e)

        # --- Exemple d'envoi d'email (avec fonction utilitaire de votre projet) ---
        # from apps.core.utils import send_email
        # send_email(
        #     subject=f"[IntelliOLT] Alerte {instance.severity} - {instance.rule.name}",
        #     message=instance.message,
        #     recipient_list=['admin@intelliolt.tn']
        # )