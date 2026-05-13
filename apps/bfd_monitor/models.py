"""
apps/bfd_monitor/models.py — BFD Session monitoring unifié avec OLT, liens fibre, interfaces,
historique d'états, planification et alertes.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel, SoftDeleteModel
from apps.equipements.models import OLT, FibreLink, NetworkInterface


class BFDSession(BaseModel):
    """
    Session BFD unifiée : peut être liée à un lien fibre (entre deux OLT)
    ou directement entre deux interfaces d'OLT.
    """
    class State(models.TextChoices):
        UP = 'up', '✅ UP'
        DOWN = 'down', '🔴 DOWN'
        INIT = 'init', '🟡 INIT'
        ADMIN_DOWN = 'admin_down', '⚫ Admin Down'

    class DiagCode(models.IntegerChoices):
        NO_DIAG = 0, 'Aucun diagnostic'
        CTRL_DETECT_EXPIRED = 1, 'Délai de détection expiré'
        ECHO_FAILED = 2, 'Fonction Echo en échec'
        NEIGHBOR_DOWN = 3, 'Session voisine signalée DOWN'
        FWD_PLANE_RESET = 4, 'Réinitialisation du plan de forwarding'
        PATH_DOWN = 5, 'Chemin en panne'
        CONCAT_PATH_DOWN = 6, 'Chemin concaténé en panne'
        ADMIN_DOWN_DIAG = 7, 'Administrativement DOWN'
        REV_CONCAT_PATH_DOWN = 8, 'Chemin concaténé inverse en panne'

    class SessionType(models.TextChoices):
        SINGLE_HOP = 'single_hop', 'Single Hop'
        MULTI_HOP = 'multi_hop', 'Multi Hop'
        ECHO = 'echo', 'Echo'

    # Identification
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom de la session")
    description = models.TextField(blank=True, verbose_name="Description")

    # Liens avec l'infrastructure (au moins une des deux relations est remplie)
    link = models.ForeignKey(
        FibreLink, on_delete=models.CASCADE, related_name='bfd_sessions',
        null=True, blank=True, verbose_name="Lien fibre associé"
    )
    olt = models.ForeignKey(
        OLT, on_delete=models.CASCADE, related_name='bfd_sessions',
        null=True, blank=True, verbose_name="OLT (pour session directe)"
    )
    interface_a = models.ForeignKey(
        NetworkInterface, on_delete=models.CASCADE,
        related_name='bfd_sessions_a', verbose_name="Interface A"
    )
    interface_b = models.ForeignKey(
        NetworkInterface, on_delete=models.CASCADE,
        related_name='bfd_sessions_b', verbose_name="Interface B"
    )

    # Adresses IP pour les sessions multihop
    peer_ip = models.GenericIPAddressField(null=True, blank=True, help_text="IP du pair BFD")
    local_ip = models.GenericIPAddressField(null=True, blank=True, help_text="IP locale BFD")
    vrf = models.CharField(max_length=50, blank=True, verbose_name="VRF")

    # Discriminateurs
    local_discriminator = models.BigIntegerField(unique=True, verbose_name="Discriminateur local")
    remote_discriminator = models.BigIntegerField(default=0, verbose_name="Discriminateur distant")

    # Paramètres BFD
    session_type = models.CharField(
        max_length=15, choices=SessionType.choices, default=SessionType.SINGLE_HOP,
        verbose_name="Type de session"
    )
    desired_tx_interval_ms = models.IntegerField(
        default=100, validators=[MinValueValidator(50)],
        verbose_name="Intervalle TX souhaité (ms)"
    )
    required_rx_interval_ms = models.IntegerField(
        default=100, validators=[MinValueValidator(50)],
        verbose_name="Intervalle RX requis (ms)"
    )
    detection_multiplier = models.IntegerField(
        default=3, validators=[MinValueValidator(2), MaxValueValidator(50)],
        verbose_name="Multiplicateur de détection"
    )
    actual_tx_interval_ms = models.IntegerField(null=True, blank=True, verbose_name="Intervalle TX négocié (ms)")
    actual_rx_interval_ms = models.IntegerField(null=True, blank=True, verbose_name="Intervalle RX négocié (ms)")

    # État
    state = models.CharField(
        max_length=15, choices=State.choices, default=State.DOWN, db_index=True,
        verbose_name="État BFD"
    )
    diagnostic = models.IntegerField(
        choices=DiagCode.choices, default=DiagCode.NO_DIAG,
        verbose_name="Code diagnostic"
    )
    last_state_change = models.DateTimeField(null=True, blank=True, verbose_name="Dernier changement d'état")
    uptime_seconds = models.BigIntegerField(null=True, blank=True, verbose_name="Uptime (secondes)")
    remote_state = models.CharField(
        max_length=15, choices=State.choices, null=True, blank=True,
        verbose_name="État distant"
    )

    # Métriques de performance
    packets_sent = models.BigIntegerField(default=0, verbose_name="Paquets envoyés")
    packets_received = models.BigIntegerField(default=0, verbose_name="Paquets reçus")
    packets_lost = models.BigIntegerField(default=0, verbose_name="Paquets perdus")
    loss_rate_pct = models.FloatField(default=0.0, verbose_name="Taux de perte (%)")
    last_update = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    # Compteurs de disponibilité
    up_count = models.IntegerField(default=0, verbose_name="Nombre de fois UP")
    down_count = models.IntegerField(default=0, verbose_name="Nombre de fois DOWN")
    flap_count = models.IntegerField(default=0, verbose_name="Nombre de flapping")
    last_up_at = models.DateTimeField(null=True, blank=True, verbose_name="Dernier passage UP")
    last_down_at = models.DateTimeField(null=True, blank=True, verbose_name="Dernier passage DOWN")

    # Configuration
    is_enabled = models.BooleanField(default=True, verbose_name="Session active")
    is_monitored = models.BooleanField(default=True, verbose_name="Surveillée")
    snmp_oid_state = models.CharField(max_length=200, blank=True, verbose_name="OID SNMP optionnel")

    class Meta:
        db_table = "bfd_sessions"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["state"]),
            models.Index(fields=["link"]),
            models.Index(fields=["olt"]),
            models.Index(fields=["interface_a", "interface_b"]),
        ]

    def __str__(self):
        if self.link:
            return f"BFD {self.link.name} [{self.get_state_display()}]"
        elif self.olt:
            return f"BFD {self.olt.hostname} ↔ {self.peer_ip} [{self.get_state_display()}]"
        else:
            return f"BFD {self.name} [{self.get_state_display()}]"

    @property
    def detect_time_ms(self):
        """Temps de détection en millisecondes (TX * multiplier)"""
        interval = self.actual_tx_interval_ms or self.desired_tx_interval_ms
        return interval * self.detection_multiplier

    @property
    def is_up(self):
        return self.state == self.State.UP

    @property
    def availability_pct(self):
        total = self.up_count + self.down_count
        return round(self.up_count / total * 100, 2) if total else 100.0

    @property
    def flap_rate(self):
        total = self.up_count + self.down_count
        return round(self.flap_count / total * 100, 1) if total else 0.0


class BFDStateHistory(BaseModel):
    """Historique des changements d'état BFD."""
    session = models.ForeignKey(BFDSession, on_delete=models.CASCADE, related_name='history')
    previous_state = models.CharField(max_length=15, choices=BFDSession.State.choices)
    new_state = models.CharField(max_length=15, choices=BFDSession.State.choices)
    diagnostic = models.IntegerField(choices=BFDSession.DiagCode.choices, default=BFDSession.DiagCode.NO_DIAG)
    duration_previous_ms = models.BigIntegerField(null=True, blank=True, help_text="Durée de l'état précédent en ms")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    triggered_alert = models.BooleanField(default=False, help_text="A déclenché une alerte ?")

    class Meta:
        db_table = "bfd_state_history"
        ordering = ["-timestamp"]
        indexes = [models.Index(fields=["session", "-timestamp"])]

    def __str__(self):
        return f"{self.session} : {self.previous_state}→{self.new_state} @ {self.timestamp:%H:%M:%S}"


class BFDPollingSchedule(BaseModel):
    """Planification de polling BFD par OLT (si session liée à un lien ou OLT)."""
    olt = models.OneToOneField(OLT, on_delete=models.CASCADE, related_name='bfd_schedule')
    poll_interval_seconds = models.IntegerField(default=30, validators=[MinValueValidator(5)])
    is_active = models.BooleanField(default=True)
    last_polled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "bfd_polling_schedules"

    def __str__(self):
        return f"BFD Schedule {self.olt.hostname} ({self.poll_interval_seconds}s)"


class BFDThresholdRule(BaseModel):
    """Règle d'alerte sur les métriques BFD."""
    SEVERITY_CHOICES = [("warning", "Warning"), ("critical", "Critical")]
    METRIC_CHOICES = [
        ("loss_rate", "Taux de perte (%)"),
        ("detect_time", "Temps de détection (ms)"),
        ("flap_rate", "Taux de flapping (%)"),
        ("availability", "Disponibilité (%)"),
        ("state_down", "Changement d'état vers DOWN"),
    ]
    OPERATOR_CHOICES = [(">", ">"), ("<", "<"), ("=", "="), (">=", ">="), ("<=", "<=")]

    name = models.CharField(max_length=100, verbose_name="Nom de la règle")
    metric = models.CharField(max_length=20, choices=METRIC_CHOICES, verbose_name="Métrique surveillée")
    operator = models.CharField(max_length=2, choices=OPERATOR_CHOICES, default=">")
    threshold = models.FloatField(verbose_name="Seuil")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="warning")
    message = models.CharField(max_length=255, verbose_name="Message d'alerte")
    is_active = models.BooleanField(default=True)
    cooldown_minutes = models.IntegerField(default=10, help_text="Délai avant ré-émission")

    class Meta:
        db_table = "bfd_threshold_rules"
        ordering = ["severity", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_metric_display()} {self.operator} {self.threshold})"


class BFDActiveAlert(BaseModel):
    """Alerte BFD en cours (active, acquittée ou résolue)."""
    STATUS_CHOICES = [("active", "Active"), ("acknowledged", "Acquittée"), ("resolved", "Résolue")]

    rule = models.ForeignKey(BFDThresholdRule, on_delete=models.CASCADE, related_name="alerts")
    session = models.ForeignKey(BFDSession, on_delete=models.CASCADE, related_name="alerts")
    value = models.FloatField(null=True, blank=True, verbose_name="Valeur ayant déclenché l'alerte")
    message = models.TextField(verbose_name="Message d'alerte")
    severity = models.CharField(max_length=20, choices=BFDThresholdRule.SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active", db_index=True)
    first_seen = models.DateTimeField(auto_now_add=True, db_index=True)
    last_seen = models.DateTimeField(auto_now=True)
    acknowledged_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    cleared_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "bfd_alerts"
        ordering = ["-first_seen"]
        indexes = [models.Index(fields=["session", "status"])]

    def __str__(self):
        return f"{self.severity}: {self.rule.name} sur {self.session}"
