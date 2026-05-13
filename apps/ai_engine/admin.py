from django.contrib import admin
from .models import MLModel, AnomalyDetection, Prediction, TrainingJob, InferenceLog

def register_admin():
    @admin.register(MLModel)
    class MLModelAdmin(admin.ModelAdmin):
        list_display = ['name', 'model_type', 'version', 'status', 'is_active', 'last_trained_at']
        list_filter = ['model_type', 'status', 'is_active']
        search_fields = ['name', 'description']
        readonly_fields = ['created_at', 'updated_at', 'last_trained_at']

    @admin.register(AnomalyDetection)
    class AnomalyDetectionAdmin(admin.ModelAdmin):
        list_display = ['metric_name', 'olt', 'ont', 'actual_value', 'anomaly_score', 'severity', 'detected_at']
        list_filter = ['severity', 'resolved']
        search_fields = ['metric_name', 'olt__hostname', 'ont__serial_number']
        raw_id_fields = ['olt', 'ont', 'interface', 'oid', 'model']
        date_hierarchy = 'detected_at'

    @admin.register(Prediction)
    class PredictionAdmin(admin.ModelAdmin):
        list_display = ['metric_name', 'olt', 'predicted_value', 'prediction_time', 'model']
        list_filter = ['model']
        search_fields = ['metric_name', 'olt__hostname']
        raw_id_fields = ['olt', 'ont', 'model']
        date_hierarchy = 'prediction_time'

    @admin.register(TrainingJob)
    class TrainingJobAdmin(admin.ModelAdmin):
        list_display = ['model', 'status', 'started_at', 'finished_at', 'samples_count']
        list_filter = ['status']
        raw_id_fields = ['model']
        readonly_fields = ['started_at', 'finished_at']

    @admin.register(InferenceLog)
    class InferenceLogAdmin(admin.ModelAdmin):
        list_display = ['model', 'success', 'inference_time_ms', 'timestamp']
        list_filter = ['success']
        raw_id_fields = ['model']
        readonly_fields = ['timestamp']
