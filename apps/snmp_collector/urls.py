from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('oids', views.SnmpOIDViewSet)
router.register('polling-profiles', views.PollingProfileViewSet)
router.register('device-profiles', views.DeviceProfileViewSet)
router.register('metrics', views.MetricHistoryViewSet)
router.register('jobs', views.PollJobViewSet)
router.register('threshold-rules', views.SnmpThresholdRuleViewSet)
router.register('alerts', views.SnmpAlertViewSet)
router.register('errors', views.SnmpErrorLogViewSet)  # si vous voulez exposer les erreurs

urlpatterns = router.urls