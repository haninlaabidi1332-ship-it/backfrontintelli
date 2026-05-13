from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('rules', views.AlertRuleViewSet)
router.register('alerts', views.AlertViewSet)
router.register('channels', views.NotificationChannelViewSet)

urlpatterns = router.urls