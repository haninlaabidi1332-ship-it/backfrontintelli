from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# IMPORTANT: basename est obligatoire car le queryset de UserViewSet est dynamique
router.register('users', views.UserViewSet, basename='user')
router.register('teams', views.TeamViewSet, basename='team')
router.register('roles', views.RoleViewSet, basename='role')
router.register('permissions', views.PermissionViewSet, basename='permission')
router.register('activities', views.UserActivityViewSet, basename='useractivity')

urlpatterns = router.urls