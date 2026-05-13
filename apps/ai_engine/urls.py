from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('models', views.MLModelViewSet)
router.register('anomalies', views.AnomalyDetectionViewSet)
router.register('predictions', views.PredictionViewSet)
router.register('training-jobs', views.TrainingJobViewSet)
router.register('inference-logs', views.InferenceLogViewSet)

urlpatterns = router.urls