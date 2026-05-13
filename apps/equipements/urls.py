# apps/equipements/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('vendors', views.VendorViewSet)
router.register('gouvernorats', views.GouvernoratViewSet)
router.register('delegations', views.DelegationViewSet)
router.register('sites', views.SiteViewSet)
router.register('racks', views.RackViewSet)
router.register('device-types', views.DeviceTypeViewSet)
router.register('olts', views.OLTViewSet)
router.register('boards', views.BoardViewSet)
router.register('interfaces', views.NetworkInterfaceViewSet)
router.register('ip-addresses', views.IPAddressViewSet)
router.register('vlans', views.VLANViewSet)
router.register('gpon-ports', views.GponPortViewSet)
router.register('splitters', views.SplitterViewSet)
router.register('splitter-ports', views.SplitterPortViewSet)
router.register('customers', views.CustomerViewSet)
router.register('onts', views.ONTViewSet)
router.register('optical-paths', views.OpticalPathViewSet)
router.register('fiber-cables', views.FiberCableViewSet)
router.register('fiber-cores', views.FiberCoreViewSet)
router.register('fibre-links', views.FibreLinkViewSet)
router.register('power-supplies', views.PowerSupplyViewSet)
router.register('fan-modules', views.FanModuleViewSet)
router.register('config-backups', views.ConfigurationBackupViewSet)
router.register('equipment-history', views.EquipmentHistoryViewSet)

urlpatterns = router.urls