"""
apps/ai_engine/models.py — Modèles pour IA/ML : anomalies, prédictions, modèles, entraînement.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel
from apps.equipements.models import OLT, ONT, NetworkInterface
from apps.snmp_collector.models import SnmpOID


class MLModel(BaseModel):
    """
    Modèle de Machine Learning enregistré (fichier pickle, joblib, ou référence externe).
    """
    class ModelType(models.TextChoices):
        ISOLATION_FOREST = 'isolation_forest', 'Isolation Forest'
        RANDOM_FOREST = 'random_forest', 'Random Forest'
        LSTM = 'lstm', 'LSTM (deep learning)'
        PROPHET = 'prophet', 'Prophet (prédiction série temporelle)'
        GROK = 'grok', 'Grok (xAI)'

    class Status(models.TextChoices):
        PENDING = 'pending', 'En attente'
        TRAINING = 'training', 'Entraînement en cours'
        ACTIVE = 'active', 'Actif'
        FAILED = 'failed', 'Échec'
        ARCHIVED = 'archived', 'Archivé'

    name = models.CharField(max_length=100, unique=True)
    model_type = models.CharField(max_length=20, choices=ModelType.choices)
    version = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    file_path = models.CharField(max_length=500, blank=True, help_text="Chemin du fichier modèle (pickle/joblib/h5)")
    parameters = models.JSONField(default=dict, help_text="Hyperparamètres du modèle")
    features = models.JSONField(default=list, help_text="Liste des features utilisées (noms d'OIDs ou métriques)")
    target_metric = models.CharField(max_length=200, blank=True, help_text="Métrique cible pour les prédictions")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    accuracy_score = models.FloatField(null=True, blank=True)
    last_trained_at = models.DateTimeField(null=True, blank=True)
    trained_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=False, help_text="Modèle actif pour les inférences")

    class Meta:
        db_table = 'ai_ml_models'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_model_type_display()} v{self.version})"


class AnomalyDetection(BaseModel):
    """
    Détection d'anomalie sur une métrique SNMP ou BFD.
    """
    class Severity(models.TextChoices):
        LOW = 'low', 'Faible'
        MEDIUM = 'medium', 'Moyenne'
        HIGH = 'high', 'Élevée'
        CRITICAL = 'critical', 'Critique'

    olt = models.ForeignKey(OLT, on_delete=models.CASCADE, related_name='anomalies', null=True, blank=True)
    ont = models.ForeignKey(ONT, on_delete=models.CASCADE, related_name='anomalies', null=True, blank=True)
    interface = models.ForeignKey(NetworkInterface, on_delete=models.CASCADE, null=True, blank=True)
    oid = models.ForeignKey(SnmpOID, on_delete=models.SET_NULL, null=True, blank=True)
    metric_name = models.CharField(max_length=200, help_text="Nom de la métrique (ex: cpu_usage)")
    expected_value = models.FloatField(null=True, blank=True)
    actual_value = models.FloatField()
    anomaly_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM)
    explanation = models.TextField(blank=True, help_text="Explication textuelle (ex: via Grok)")
    detected_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    model = models.ForeignKey(MLModel, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'ai_anomaly_detections'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['olt', '-detected_at']),
            models.Index(fields=['severity']),
        ]

    def __str__(self):
        return f"Anomalie {self.metric_name}={self.actual_value} (score={self.anomaly_score}) sur {self.olt or self.ont or self.interface}"


class Prediction(BaseModel):
    """
    Prédiction (prévision) pour une métrique donnée (ex: charge CPU future).
    """
    olt = models.ForeignKey(OLT, on_delete=models.CASCADE, related_name='predictions', null=True, blank=True)
    ont = models.ForeignKey(ONT, on_delete=models.CASCADE, related_name='predictions', null=True, blank=True)
    metric_name = models.CharField(max_length=200)
    predicted_at = models.DateTimeField(auto_now_add=True)
    prediction_time = models.DateTimeField(help_text="Horodatage de la prédiction (moment futur)")
    predicted_value = models.FloatField()
    lower_bound = models.FloatField(null=True, blank=True)
    upper_bound = models.FloatField(null=True, blank=True)
    confidence_interval = models.FloatField(default=0.95, help_text="Niveau de confiance")
    model = models.ForeignKey(MLModel, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'ai_predictions'
        ordering = ['-predicted_at']
        indexes = [models.Index(fields=['olt', 'prediction_time'])]

    def __str__(self):
        return f"Prédiction {self.metric_name}={self.predicted_value} @ {self.prediction_time}"


class TrainingJob(BaseModel):
    """
    Historique des entraînements de modèles ML.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'En attente'
        RUNNING = 'running', 'En cours'
        SUCCESS = 'success', 'Succès'
        FAILED = 'failed', 'Échec'

    model = models.ForeignKey(MLModel, on_delete=models.CASCADE, related_name='training_jobs')
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    metrics = models.JSONField(default=dict, help_text="Métriques d'évaluation (accuracy, loss, etc.)")
    error_message = models.TextField(blank=True)
    data_start_date = models.DateTimeField(help_text="Début des données d'entraînement")
    data_end_date = models.DateTimeField(help_text="Fin des données d'entraînement")
    samples_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'ai_training_jobs'
        ordering = ['-started_at']


class InferenceLog(BaseModel):
    """
    Journal des inférences (pour audit et debug).
    """
    model = models.ForeignKey(MLModel, on_delete=models.SET_NULL, null=True, blank=True)
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    inference_time_ms = models.FloatField()
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'ai_inference_logs'
        ordering = ['-timestamp']