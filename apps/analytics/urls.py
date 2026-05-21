from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('kpis', views.KPIViewSet)
router.register('reports', views.ReportViewSet)
router.register('dashboard-widgets', views.DashboardWidgetViewSet, basename='dashboard-widget')

# New data collection endpoints
router.register('network-devices', views.NetworkDeviceViewSet, basename='network-device')
router.register('topology-links', views.TopologyLinkViewSet, basename='topology-link')
router.register('ssh-metrics', views.SSHMetricsSnapshotViewSet, basename='ssh-metrics')
router.register('network-traffic', views.NetworkTrafficViewSet, basename='network-traffic')

urlpatterns = router.urls