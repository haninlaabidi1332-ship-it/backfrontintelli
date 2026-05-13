from rest_framework import serializers
from .models import EveNgLab, EveNgDevice, EveNgLabExecution

class EveNgLabSerializer(serializers.ModelSerializer):
    class Meta:
        model = EveNgLab
        fields = '__all__'

class EveNgDeviceSerializer(serializers.ModelSerializer):
    lab_name = serializers.CharField(source='lab.name', read_only=True)
    olt_hostname = serializers.CharField(source='olt.hostname', read_only=True)
    class Meta:
        model = EveNgDevice
        fields = '__all__'

class EveNgLabExecutionSerializer(serializers.ModelSerializer):
    lab_name = serializers.CharField(source='lab.name', read_only=True)
    class Meta:
        model = EveNgLabExecution
        fields = '__all__'