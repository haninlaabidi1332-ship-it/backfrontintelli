from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('labs', views.EveNgLabViewSet)
router.register('devices', views.EveNgDeviceViewSet)

urlpatterns = router.urls