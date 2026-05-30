from rest_framework import serializers
from .models import MLModel, AnomalyDetection, Prediction, TrainingJob, InferenceLog


class MLModelSerializer(serializers.ModelSerializer):
    model_type_display = serializers.CharField(source='get_model_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MLModel
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_trained_at']


class AnomalyDetectionSerializer(serializers.ModelSerializer):
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True, allow_null=True)
    interface_name = serializers.CharField(source='interface.name', read_only=True, allow_null=True)
    oid_name = serializers.CharField(source='oid.name', read_only=True, allow_null=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)

    class Meta:
        model = AnomalyDetection
        fields = '__all__'
        read_only_fields = ['id', 'detected_at']


class PredictionSerializer(serializers.ModelSerializer):
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True, allow_null=True)

    class Meta:
        model = Prediction
        fields = '__all__'
        read_only_fields = ['id', 'predicted_at']


class TrainingJobSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(source='model.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = TrainingJob
        fields = '__all__'
        read_only_fields = ['id', 'started_at']


class InferenceLogSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(source='model.name', read_only=True, allow_null=True)

    class Meta:
        model = InferenceLog
        fields = '__all__'
        read_only_fields = ['id', 'timestamp']