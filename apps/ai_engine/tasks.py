import logging
import numpy as np
import pandas as pd
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os

logger = logging.getLogger(__name__)


# --- Helper d'intégration Grok (xAI) ---
def call_grok_api(prompt: str, system_prompt: str = None) -> str:
    """
    Appelle l'API Grok (xAI) pour obtenir une explication textuelle.
    Nécessite les variables d'environnement GROK_API_KEY, GROK_API_ENDPOINT, GROK_MODEL.
    """
    import requests
    from django.conf import settings

    api_key = getattr(settings, 'GROK_API_KEY', '')
    endpoint = getattr(settings, 'GROK_API_ENDPOINT', 'https://api.x.ai/v1/chat/completions')
    model = getattr(settings, 'GROK_MODEL', 'grok-4.20-reasoning')

    if not api_key:
        logger.warning("GROK_API_KEY non configurée, retour du prompt simple")
        return f"Explication non disponible (clé API manquante). Données : {prompt}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        response = requests.post(endpoint, json={
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500
        }, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        logger.error("Erreur appel Grok: %s", e)
        return f"Erreur d'appel à l'IA : {str(e)}"


# --- Entraînement d'un modèle Isolation Forest ---
@shared_task(name='ai.train_model')
def train_model(model_id, data_start, data_end):
    from .models import MLModel, TrainingJob, AnomalyDetection
    from apps.snmp_collector.models import MetricHistory
    from apps.equipements.models import OLT

    try:
        model_obj = MLModel.objects.get(id=model_id)
    except MLModel.DoesNotExist:
        logger.error("Modèle %s introuvable", model_id)
        return

    job = TrainingJob.objects.create(
        model=model_obj,
        status=TrainingJob.Status.RUNNING,
        data_start_date=data_start,
        data_end_date=data_end
    )
    model_obj.status = MLModel.Status.TRAINING
    model_obj.save()

    try:
        # Récupération des données d'entraînement (ex: métriques SNMP)
        # Ici, on suppose que le modèle utilise des OIDs spécifiques (model_obj.features)
        features = model_obj.features or []
        if not features:
            raise ValueError("Aucune feature définie pour ce modèle")

        # Exemple : collecter les métriques pour tous les OLT (ou un OLT spécifique)
        metrics = MetricHistory.objects.filter(
            timestamp__gte=data_start, timestamp__lte=data_end,
            oid__name__in=features, numeric_value__isnull=False
        ).select_related('oid').order_by('olt', 'timestamp')

        if not metrics.exists():
            raise ValueError("Pas assez de données pour l'entraînement")

        # Transformation en DataFrame
        data = []
        for metric in metrics:
            data.append({
                'olt_id': metric.olt_id,
                'timestamp': metric.timestamp,
                metric.oid.name: metric.numeric_value
            })
        df = pd.DataFrame(data)
        # Pivot pour avoir une colonne par feature
        df_pivot = df.pivot_table(index=['olt_id', 'timestamp'], columns='oid_name', values='value').reset_index()
        X = df_pivot[features].dropna()

        if len(X) < 100:
            raise ValueError(f"Données insuffisantes : {len(X)} échantillons (min 100 requis)")

        # Normalisation
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Entraînement Isolation Forest
        clf = IsolationForest(contamination=0.1, random_state=42)
        clf.fit(X_scaled)

        # Sauvegarde du modèle et du scaler
        model_dir = os.path.join(settings.MEDIA_ROOT, 'ai_models')
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, f"{model_obj.name}_v{model_obj.version}.joblib")
        scaler_path = os.path.join(model_dir, f"{model_obj.name}_v{model_obj.version}_scaler.joblib")
        joblib.dump(clf, model_path)
        joblib.dump(scaler, scaler_path)

        model_obj.file_path = model_path
        model_obj.status = MLModel.Status.ACTIVE
        model_obj.is_active = True
        model_obj.last_trained_at = timezone.now()
        model_obj.accuracy_score = None  # Isolation Forest n'a pas d'accuracy directe
        model_obj.save()

        job.status = TrainingJob.Status.SUCCESS
        job.finished_at = timezone.now()
        job.samples_count = len(X)
        job.metrics = {'contamination': 0.1, 'n_estimators': 100}
        job.save()

        logger.info("Entraînement du modèle %s terminé avec %d échantillons", model_obj.name, len(X))

    except Exception as e:
        logger.exception("Échec de l'entraînement du modèle %s", model_obj.name)
        model_obj.status = MLModel.Status.FAILED
        model_obj.save()
        job.status = TrainingJob.Status.FAILED
        job.finished_at = timezone.now()
        job.error_message = str(e)
        job.save()


# --- Détection d'anomalies pour un OLT ---
@shared_task(name='ai.detect_anomalies')
def detect_anomalies_for_olt(olt_id, model_id=None):
    from .models import MLModel, AnomalyDetection, InferenceLog
    from apps.snmp_collector.models import MetricHistory
    from apps.equipements.models import OLT
    import joblib
    import time

    start_time = time.time()
    try:
        olt = OLT.objects.get(id=olt_id)
    except OLT.DoesNotExist:
        logger.error("OLT %s introuvable", olt_id)
        return

    # Récupérer le modèle actif pour le type 'isolation_forest' ou spécifié
    if model_id:
        model_obj = MLModel.objects.filter(id=model_id, is_active=True).first()
    else:
        model_obj = MLModel.objects.filter(model_type='isolation_forest', is_active=True).first()

    if not model_obj or not model_obj.file_path:
        logger.warning("Aucun modèle actif pour la détection d'anomalies")
        return

    try:
        clf = joblib.load(model_obj.file_path)
        scaler_path = model_obj.file_path.replace('.joblib', '_scaler.joblib')
        scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None

        features = model_obj.features
        if not features:
            raise ValueError("Aucune feature définie pour le modèle")

        # Récupérer les dernières métriques (ex: dernière heure)
        since = timezone.now() - timedelta(hours=1)
        metrics = MetricHistory.objects.filter(
            olt=olt, timestamp__gte=since,
            oid__name__in=features, numeric_value__isnull=False
        ).select_related('oid').order_by('timestamp')

        if not metrics.exists():
            logger.info("Aucune métrique récente pour l'OLT %s", olt.hostname)
            return

        # Grouper par timestamp
        data = {}
        for m in metrics:
            key = m.timestamp
            if key not in data:
                data[key] = {}
            data[key][m.oid.name] = m.numeric_value

        # Pour chaque point temporel
        for ts, values in data.items():
            # Vérifier que toutes les features sont présentes
            missing = [f for f in features if f not in values]
            if missing:
                continue
            X = np.array([[values[f] for f in features]])
            if scaler:
                X = scaler.transform(X)
            score = clf.decision_function(X)[0]  # plus proche de 0 = normal, négatif = anomalie
            anomaly_score = 1 - (score + 1) / 2  # conversion en [0,1] (1=anormal)
            if anomaly_score > 0.6:  # seuil
                # Créer une anomalie si elle n'existe pas déjà pour cette métrique récente
                # On peut prendre la métrique la plus aberrante (ou toutes)
                # Simplification : on enregistre une anomalie par OLT avec la première métrique
                existing = AnomalyDetection.objects.filter(
                    olt=olt, detected_at__gte=ts - timedelta(minutes=5)
                ).exists()
                if not existing:
                    # Sélectionner la métrique avec la plus grande deviation (pour affichage)
                    # Ici on prend la première feature
                    actual_value = values[features[0]]
                    explanation = f"Détection d'anomalie par {model_obj.name} (score={anomaly_score:.2f})"
                    # Optionnel : appeler Grok pour une explication
                    if getattr(settings, 'GROK_API_KEY', None):
                        grok_prompt = f"Explique cette anomalie sur l'OLT {olt.hostname}: la métrique {features[0]} a une valeur de {actual_value} alors que la normale est autour de ... (score d'anomalie {anomaly_score:.2f})"
                        explanation += " " + call_grok_api(grok_prompt)
                    AnomalyDetection.objects.create(
                        olt=olt,
                        metric_name=features[0],
                        actual_value=actual_value,
                        anomaly_score=anomaly_score,
                        severity='medium' if anomaly_score > 0.8 else 'low',
                        explanation=explanation,
                        model=model_obj
                    )
                    logger.info("Anomalie détectée sur OLT %s: %s=%.2f (score=%.2f)", olt.hostname, features[0], actual_value, anomaly_score)

        # Log d'inférence
        InferenceLog.objects.create(
            model=model_obj,
            input_data={'olt_id': olt_id, 'features': features},
            output_data={'anomalies_detected': AnomalyDetection.objects.filter(olt=olt, detected_at__gte=since).count()},
            inference_time_ms=(time.time() - start_time) * 1000,
            success=True
        )

    except Exception as e:
        logger.exception("Erreur lors de la détection d'anomalies pour OLT %s", olt_id)
        InferenceLog.objects.create(
            model=model_obj if 'model_obj' in locals() else None,
            input_data={'olt_id': olt_id},
            output_data={},
            inference_time_ms=(time.time() - start_time) * 1000,
            success=False,
            error_message=str(e)
        )


# --- Prédiction (ex: avec Prophet ou LSTM) ---
@shared_task(name='ai.predict_metric')
def predict_metric(olt_id, metric_name, horizon_hours=24):
    from .models import Prediction, MLModel
    from apps.snmp_collector.models import MetricHistory
    from apps.snmp_collector.models import SnmpOID
    from apps.equipements.models import OLT
    from prophet import Prophet
    import pandas as pd

    try:
        olt = OLT.objects.get(id=olt_id)
        oid = SnmpOID.objects.filter(name=metric_name).first()
        if not oid:
            logger.error("OID non trouvé pour métrique %s", metric_name)
            return

        # Récupérer l'historique des métriques (ex: 30 jours)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        metrics = MetricHistory.objects.filter(
            olt=olt, oid=oid, timestamp__gte=start_date, numeric_value__isnull=False
        ).order_by('timestamp').values_list('timestamp', 'numeric_value')

        if metrics.count() < 50:
            logger.warning("Pas assez de données pour la prédiction sur %s", metric_name)
            return

        df = pd.DataFrame(list(metrics), columns=['ds', 'y'])
        df['ds'] = pd.to_datetime(df['ds'])

        # Utiliser Prophet
        model = Prophet()
        model.fit(df)

        # Créer un dataframe futur
        future = model.make_future_dataframe(periods=horizon_hours, freq='H')
        forecast = model.predict(future)

        # Enregistrer les prédictions futures
        last_timestamp = df['ds'].max()
        forecast_future = forecast[forecast['ds'] > last_timestamp]

        for _, row in forecast_future.iterrows():
            Prediction.objects.create(
                olt=olt,
                metric_name=metric_name,
                prediction_time=row['ds'],
                predicted_value=row['yhat'],
                lower_bound=row['yhat_lower'],
                upper_bound=row['yhat_upper'],
                confidence_interval=0.95
            )

        logger.info("Prédictions pour %s sur OLT %s: %d points générés", metric_name, olt.hostname, len(forecast_future))

    except Exception as e:
        logger.exception("Erreur lors de la prédiction pour OLT %s", olt_id)


# --- Détection périodique pour tous les OLT ---
@shared_task(name='ai.detect_all_anomalies')
def detect_all_anomalies():
    from apps.equipements.models import OLT
    olt_ids = OLT.objects.filter(status__in=['active', 'degraded']).values_list('id', flat=True)
    for olt_id in olt_ids:
        detect_anomalies_for_olt.delay(olt_id)
    logger.info("detect_all_anomalies: %d OLTs planifiés", len(olt_ids))
    return {"scheduled": len(olt_ids)}


def register_beat_schedule():
    """
    Enregistre les tâches périodiques dans Celery Beat.
    Appelé dans apps.py.
    """
    from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule

    # Détection d'anomalies toutes les 5 minutes
    interval, _ = IntervalSchedule.objects.get_or_create(every=5, period=IntervalSchedule.MINUTES)
    PeriodicTask.objects.get_or_create(
        name='detect_all_anomalies',
        task='ai.detect_all_anomalies',
        interval=interval,
        defaults={'enabled': True}
    )

    # Entraînement hebdomadaire (ex: dimanche à 3h du matin)
    cron, _ = CrontabSchedule.objects.get_or_create(minute='0', hour='3', day_of_week='sun')
    # On ne crée pas de tâche d'entraînement automatique par défaut (à paramétrer)