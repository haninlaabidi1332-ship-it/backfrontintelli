# apps/equipements/signals.py
import logging
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import OLT, ONT

logger = logging.getLogger(__name__)


# ============================================================================
# SIGNAUX POUR OLT
# ============================================================================

@receiver(post_save, sender=OLT)
def log_olt_save(sender, instance, created, **kwargs):
    """Journalise la création ou modification d'un OLT."""
    if created:
        logger.info(f"➕ OLT créé: {instance.hostname} ({instance.ip_address})")
    else:
        logger.info(f"✏️ OLT modifié: {instance.hostname} ({instance.ip_address})")


@receiver(post_delete, sender=OLT)
def log_olt_delete(sender, instance, **kwargs):
    """Journalise la suppression (soft-delete) d'un OLT."""
    logger.info(f"🗑️ OLT supprimé: {instance.hostname}")


# ============================================================================
# SIGNAUX POUR ONT
# ============================================================================

@receiver(post_save, sender=ONT)
def log_ont_save(sender, instance, created, **kwargs):
    """Journalise la création ou modification d'un ONT."""
    if created:
        logger.info(f"➕ ONT créé: {instance.serial_number} (OLT: {instance.olt.hostname})")
    else:
        logger.info(f"✏️ ONT modifié: {instance.serial_number}")


@receiver(post_delete, sender=ONT)
def log_ont_delete(sender, instance, **kwargs):
    """Journalise la suppression (soft-delete) d'un ONT."""
    logger.info(f"🗑️ ONT supprimé: {instance.serial_number}")


# ============================================================================
# SIGNAUX POUR AUTRES MODÈLES (optionnels, à activer si besoin)
# ============================================================================

# Si vous voulez journaliser la création/modification des Boards, Splitters, etc.,
# décommentez et adaptez les blocs suivants.

# @receiver(post_save, sender=Board)
# def log_board_save(sender, instance, created, **kwargs):
#     if created:
#         logger.info(f"➕ Carte ajoutée: {instance.model} (slot {instance.slot_number}) sur OLT {instance.olt.hostname}")
#     else:
#         logger.info(f"✏️ Carte modifiée: {instance.model} sur OLT {instance.olt.hostname}")

# @receiver(post_save, sender=Splitter)
# def log_splitter_save(sender, instance, created, **kwargs):
#     if created:
#         logger.info(f"➕ Splitter créé: {instance.name} ({instance.ratio})")
#     else:
#         logger.info(f"✏️ Splitter modifié: {instance.name}")

# @receiver(post_save, sender=FibreLink)
# def log_fibre_link_save(sender, instance, created, **kwargs):
#     if created:
#         logger.info(f"🔗 Lien fibre créé: {instance.name} ({instance.interface_a.olt.hostname} ↔ {instance.interface_b.olt.hostname})")
#     else:
#         logger.info(f"✏️ Lien fibre modifié: {instance.name}")