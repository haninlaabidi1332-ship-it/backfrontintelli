import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import BFDSession, BFDActiveAlert

logger = logging.getLogger(__name__)


@receiver(post_save, sender=BFDSession)
def log_bfd_session_change(sender, instance, created, **kwargs):
    if created:
        logger.info("➕ Session BFD créée: %s", instance)
    else:
        logger.info("✏️ Session BFD modifiée: %s (état=%s)", instance, instance.state)


@receiver(post_save, sender=BFDActiveAlert)
def notify_bfd_alert(sender, instance, created, **kwargs):
    if created and instance.status == 'active':
        logger.info("🚨 Alerte BFD: %s sur %s (valeur=%s)", instance.rule.name, instance.session, instance.value)
        # Ici, intégrez votre système de notifications (email, webhook, etc.)