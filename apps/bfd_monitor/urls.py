from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('sessions', views.BFDSessionViewSet)
router.register('history', views.BFDStateHistoryViewSet)
router.register('schedules', views.BFDPollingScheduleViewSet)
router.register('threshold-rules', views.BFDThresholdRuleViewSet)
router.register('alerts', views.BFDActiveAlertViewSet)

urlpatterns = router.urls