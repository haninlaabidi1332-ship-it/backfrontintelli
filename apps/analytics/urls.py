from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('kpis', views.KPIViewSet)
router.register('reports', views.ReportViewSet)
router.register('dashboard-widgets', views.DashboardWidgetViewSet, basename='dashboard-widget')

urlpatterns = router.urls