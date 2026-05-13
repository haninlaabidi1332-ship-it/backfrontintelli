# apps/core/models.py
"""
Modèles de base abstraits pour IntelliOLT – AI-Powered Fiber Network Supervision Platform.
Fournit les fondations (UUID, timestamps, suppression logique avancée) pour toutes les applications.
"""
import uuid
from django.db import models
from django.utils import timezone


# ─────────────────────────────────────────────────────────────────────────────
#  Mixins atomiques
# ─────────────────────────────────────────────────────────────────────────────

class UUIDModel(models.Model):
    """Remplace l'auto-incrément entier par un UUID v4 non-devinable."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimestampedModel(models.Model):
    """Horodatage automatique à la création et à chaque mise à jour."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ─────────────────────────────────────────────────────────────────────────────
#  Modèle de base (UUID + timestamps)
# ─────────────────────────────────────────────────────────────────────────────

class BaseModel(UUIDModel, TimestampedModel):
    """Héritage standard pour tous les modèles métier."""
    class Meta:
        abstract = True


# ─────────────────────────────────────────────────────────────────────────────
#  Soft-delete avancé (QuerySet avec méthodes .alive(), .deleted(), .restore())
# ─────────────────────────────────────────────────────────────────────────────

class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet qui filtre les enregistrements supprimés (soft-delete)."""

    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        return self.filter(deleted_at__isnull=False)

    def delete(self):
        return self.update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def restore(self):
        return self.update(deleted_at=None)


class SoftDeleteManager(models.Manager):
    """Manager par défaut — n'expose que les enregistrements non supprimés."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    def deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db).deleted()

    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteModel(BaseModel):
    """
    Modèle avec suppression logique avancée.
    - .delete()          → soft delete (pose deleted_at)
    - .hard_delete()     → suppression physique définitive
    - .restore()         → restaure un élément soft-deleted
    - .is_deleted        → propriété booléenne
    """
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()          # Manager par défaut (exclut les soft-deleted)
    all_objects = models.Manager()         # Manager incluant tous les enregistrements

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])

    def hard_delete(self):
        super().delete()

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at", "updated_at"])

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    class Meta:
        abstract = True


# ─────────────────────────────────────────────────────────────────────────────
#  Configuration globale (paramètres système, SNMP, BFD, IA, EVE-NG)
# ─────────────────────────────────────────────────────────────────────────────

class Config(BaseModel):
    """
    Configuration globale d'IntelliOLT – Supervision OLT avec IA.
    Stocke les paramètres système, seuils SNMP, configuration BFD,
    règles d'alertes, paramètres des modèles ML, intégration EVE-NG, etc.
    """

    CONFIG_TYPES = [
        ('general', '⚙️ Général'),
        ('security', '🛡️ Sécurité / Authentification'),
        ('snmp', '📊 SNMP (polling, communautés, OIDs)'),
        ('bfd', '🔗 BFD (intervalles, multiplicateur)'),
        ('alerting', '🚨 Alertes (seuils, notifications)'),
        ('ai_engine', '🧠 IA / ML (modèles, seuils anomalie)'),
        ('eve_ng', '🧪 EVE-NG (intégration lab virtuel)'),
        ('notifications', '🔔 Notifications (email, webhook)'),
        ('exports', '📁 Exports de données (CSV, PDF)'),
        ('logs', '📜 Journalisation et rétention'),
    ]

    key = models.CharField('Clé', max_length=200, unique=True, db_index=True)
    value = models.JSONField('Valeur', default=dict)
    description = models.TextField('Description', blank=True)
    config_type = models.CharField('Type', max_length=20, choices=CONFIG_TYPES, default='general', db_index=True)
    is_encrypted = models.BooleanField('Chiffré', default=False)

    class Meta:
        db_table = 'core_config'
        verbose_name = 'Configuration IntelliOLT'
        verbose_name_plural = 'Configurations IntelliOLT'
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['config_type']),
        ]

    def __str__(self):
        return f"{self.key} ({self.get_config_type_display()})"

    def save(self, *args, **kwargs):
        # Invalider le cache lors de la sauvegarde
        from django.core.cache import cache
        cache.delete(f'config_{self.key}')
        cache.delete('config_all')
        super().save(*args, **kwargs)