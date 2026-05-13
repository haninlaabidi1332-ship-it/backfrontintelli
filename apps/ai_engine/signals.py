import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AnomalyDetection

logger = logging.getLogger(__name__)

@receiver(post_save, sender=AnomalyDetection)
def notify_anomaly(sender, instance, created, **kwargs):
    if created:
        logger.info("🧠 Nouvelle anomalie détectée: %s (score=%.2f)", instance, instance.anomaly_score)
        # Ici, intégrez un système de notification (email, webhook, etc.)
        # Exemple (si vous avez un système d'alertes):
        # from apps.alerting.models import Alert
        # Alert.objects.create(...)