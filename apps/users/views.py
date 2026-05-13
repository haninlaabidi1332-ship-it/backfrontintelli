"""
Views pour la gestion des utilisateurs IntelliOLT – AI-Powered Fiber Network Supervision Platform
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Count, Q, Max
from django.utils import timezone
from datetime import timedelta

from apps.core.permissions import (
    IsAdmin, IsSupervisor, IsOperator, IsViewer,
    IsActiveUser, HasAPIAccess,
    CanViewOLT, CanManageOLT,
    CanViewONT, CanManageONT,
    CanViewSNMPMetrics, CanManageSNMPOID,
    CanViewBFDSession, CanManageBFDSession,
    CanViewAlertRule, CanManageAlertRule,
    CanViewAlert, CanAcknowledgeAlert, CanResolveAlert,
    CanViewAnomaly, CanManageMLModel,
    CanViewDashboard, CanExportData,
    CanManageLab
)
from apps.core.responses import (
    success_response, created_response, error_response,
    not_found_response, forbidden_response
)
from apps.core.pagination import StandardPagination
from apps.core.utils import get_client_ip, Timer

from .models import User, Team, Role, Permission, UserActivity
from .serializers import (
    UserListSerializer, UserDetailSerializer, UserCreateSerializer,
    UserUpdateSerializer, UserMinimalSerializer, UserStatsSerializer,
    TeamSerializer, RoleSerializer, PermissionSerializer,
    UserActivitySerializer, ChangePasswordSerializer
)
from .filters import (
    UserFilter, TeamFilter, RoleFilter,
    PermissionFilter, UserActivityFilter
)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des utilisateurs IntelliOLT
    """

    # CORRECTION 1: expliciter lookup_field
    lookup_field = "pk"
    lookup_url_kwarg = "pk"

    # CORRECTION 2: éviter select_related() sans arguments, utiliser prefetch_related
    queryset = User.objects.prefetch_related('teams', 'activities')

    serializer_class = UserDetailSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UserFilter
    search_fields = ['username', 'email', 'first_name', 'last_name', 'employee_id']
    ordering_fields = ['created_at', 'last_login', 'username', 'email']
    ordering = ['-created_at']
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'me':
            return UserDetailSerializer
        elif self.action == 'minimal_list':
            return UserMinimalSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserDetailSerializer

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        elif self.action in ['destroy', 'bulk_delete']:
            permission_classes = [IsAuthenticated, IsAdmin]
        elif self.action in ['update', 'partial_update', 'reset_password',
                            'toggle_status', 'toggle_api_access']:
            permission_classes = [IsAuthenticated, IsAdmin]
        elif self.action == 'check_permissions':
            permission_classes = [IsAuthenticated, IsAdmin]
        elif self.action == 'minimal_list':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsActiveUser, HasAPIAccess]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return User.objects.none()
        if user.is_admin:
            return User.objects.all().prefetch_related('teams', 'activities')
        if user.is_supervisor:
            return User.objects.all().prefetch_related('teams', 'activities')
        return User.objects.filter(id=user.id).prefetch_related('teams', 'activities')

    def list(self, request, *args, **kwargs):
        timer = Timer().start()
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        timer.stop()
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            serializer.data,
            "Utilisateurs IntelliOLT récupérés avec succès",
            meta={"query_time_ms": timer.duration_ms()}
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        UserActivity.objects.create(
            user=user,
            action='create',
            description=f"Utilisateur IntelliOLT {user.email} créé",
            resource_type='user',
            resource_id=str(user.id),
            resource_name=user.get_full_name(),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        return created_response(
            UserDetailSerializer(user).data,
            "Utilisateur IntelliOLT créé avec succès"
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        UserActivity.objects.create(
            user=request.user,
            action='update',
            description=f"Utilisateur IntelliOLT {user.email} mis à jour",
            resource_type='user',
            resource_id=str(user.id),
            resource_name=user.get_full_name(),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        return success_response(
            UserDetailSerializer(user).data,
            "Utilisateur IntelliOLT mis à jour avec succès"
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.id == request.user.id:
            return error_response(
                "Vous ne pouvez pas supprimer votre propre compte",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        user_email = instance.email
        user_id = str(instance.id)
        instance.delete()
        UserActivity.objects.create(
            user=request.user,
            action='delete',
            severity='medium',
            description=f"Utilisateur IntelliOLT {user_email} supprimé",
            resource_type='user',
            resource_id=user_id,
            resource_name=instance.get_full_name(),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        return success_response(None, "Utilisateur IntelliOLT supprimé avec succès")

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = UserDetailSerializer(request.user)
        data = serializer.data
        data['session'] = {
            'last_activity': timezone.now(),
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        return success_response(data, "Profil utilisateur IntelliOLT récupéré")

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        UserActivity.objects.create(
            user=user,
            action='update',
            severity='medium',
            description="Mot de passe modifié",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        return success_response(None, "Mot de passe modifié avec succès")

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def reset_password(self, request, pk=None):
        user = self.get_object()
        # TODO: envoyer email de réinitialisation
        UserActivity.objects.create(
            user=request.user,
            action='update',
            severity='medium',
            description=f"Réinitialisation du mot de passe pour {user.email}",
            resource_type='user',
            resource_id=str(user.id),
            resource_name=user.get_full_name(),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        return success_response(None, f"Email de réinitialisation envoyé à {user.email}")

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def toggle_status(self, request, pk=None):
        user = self.get_object()
        if user.id == request.user.id:
            return error_response(
                "Vous ne pouvez pas modifier votre propre statut",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        new_status = request.data.get('status')
        if new_status not in ['active', 'inactive', 'suspended']:
            return error_response(
                "Statut invalide. Choisir parmi : active, inactive, suspended",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        old_status = user.status
        user.status = new_status
        user.is_active = new_status == 'active'
        user.save()
        UserActivity.objects.create(
            user=request.user,
            action='update',
            severity='medium' if new_status == 'suspended' else 'low',
            description=f"Statut utilisateur changé de {old_status} à {new_status}",
            resource_type='user',
            resource_id=str(user.id),
            resource_name=user.get_full_name(),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        return success_response(
            UserDetailSerializer(user).data,
            f"Statut utilisateur mis à jour : {new_status}"
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def toggle_api_access(self, request, pk=None):
        user = self.get_object()
        user.api_access_enabled = not user.api_access_enabled
        user.save()
        status_text = "activé" if user.api_access_enabled else "désactivé"
        UserActivity.objects.create(
            user=request.user,
            action='update',
            severity='low',
            description=f"Accès API {status_text} pour {user.email}",
            resource_type='user',
            resource_id=str(user.id),
            resource_name=user.get_full_name(),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        return success_response(
            {'api_access_enabled': user.api_access_enabled},
            f"Accès API {status_text}"
        )

    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        user = self.get_object()
        if not (request.user.is_admin or request.user.is_supervisor or request.user.id == user.id):
            return forbidden_response(
                "Vous n'avez pas la permission de voir ces activités",
                required_permission="admin ou supervisor"
            )
        activities = user.activities.all()
        days = request.query_params.get('days')
        if days:
            try:
                days = int(days)
                cutoff = timezone.now() - timedelta(days=days)
                activities = activities.filter(created_at__gte=cutoff)
            except ValueError:
                pass
        page = self.paginate_queryset(activities)
        if page is not None:
            serializer = UserActivitySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = UserActivitySerializer(activities, many=True)
        return success_response(serializer.data, "Activités récupérées")

    @action(detail=False, methods=['get'])
    def minimal_list(self, request):
        users = self.get_queryset()[:50]
        serializer = UserMinimalSerializer(users, many=True)
        return success_response(serializer.data, "Liste minimale des utilisateurs IntelliOLT")

    @action(detail=False, methods=['get'])
    def stats(self, request):
        if not (request.user.is_admin or request.user.is_supervisor):
            return forbidden_response(
                "Accès administrateur requis",
                required_permission="admin ou supervisor"
            )
        queryset = self.get_queryset()
        total_users = queryset.count()
        active_users = queryset.filter(status='active', is_active=True).count()
        inactive_users = queryset.filter(status='inactive').count()
        by_role = {}
        for role, _ in User.ROLE_CHOICES:
            cnt = queryset.filter(role=role).count()
            if cnt > 0:
                by_role[role] = cnt
        admins = queryset.filter(role='admin').count()
        supervisors = queryset.filter(role='supervisor').count()
        operators = queryset.filter(role='operator').count()
        viewers = queryset.filter(role='viewer').count()
        last_24h = timezone.now() - timedelta(hours=24)
        recent_activities = UserActivity.objects.filter(created_at__gte=last_24h).count()
        api_users = queryset.filter(api_access_enabled=True).count()
        stats_data = {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'by_role': by_role,
            'admins': admins,
            'supervisors': supervisors,
            'operators': operators,
            'viewers': viewers,
            'recent_activities': recent_activities,
            'api_users': api_users,
            'verified_users': queryset.filter(is_verified=True).count(),
            'two_factor_enabled': queryset.filter(two_factor_enabled=True).count(),
        }
        serializer = UserStatsSerializer(data=stats_data)
        serializer.is_valid()
        return success_response(serializer.data, "Statistiques utilisateurs IntelliOLT récupérées")

    @action(detail=True, methods=['get'])
    def check_permissions(self, request, pk=None):
        # Évite l'appel à get_object() lorsque la requête n'est pas une vue détail
        if not pk or self.kwargs.get('pk') is None:
            return error_response(
                "Cet endpoint nécessite un ID utilisateur.",
                status_code=status.HTTP_400_BAD_REQUEST
        )
        user = self.get_object()
        if not (request.user.is_admin or request.user.is_supervisor or request.user.id == user.id):
            return forbidden_response(
                "Vous n'avez pas accès à ces informations",
                required_permission="admin ou supervisor"
            )
        data = {
            'can_view_olt': user.can_view_olt,
            'can_manage_olt': user.can_manage_olt,
            'can_view_ont': user.can_view_ont,
            'can_manage_ont': user.can_manage_ont,
            'can_view_snmp_metrics': user.can_view_snmp_metrics,
            'can_manage_snmp_oids': user.can_manage_snmp_oids,
            'can_view_bfd_sessions': user.can_view_bfd_sessions,
            'can_manage_bfd_sessions': user.can_manage_bfd_sessions,
            'can_view_alert_rules': user.can_view_alert_rules,
            'can_manage_alert_rules': user.can_manage_alert_rules,
            'can_view_alerts': user.can_view_alerts,
            'can_acknowledge_alert': user.can_acknowledge_alert,
            'can_resolve_alert': user.can_resolve_alert,
            'can_view_anomalies': user.can_view_anomalies,
            'can_manage_ml_models': user.can_manage_ml_models,
            'can_view_dashboard': user.can_view_dashboard,
            'can_export_data': user.can_export_data,
            'can_manage_labs': user.can_manage_labs,
            'can_view_notifications': user.can_view_notifications,
            'can_manage_notifications': user.can_manage_notifications,
            'permissions': {
                'olt': CanViewOLT.message if not user.can_view_olt else None,
                'snmp': CanViewSNMPMetrics.message if not user.can_view_snmp_metrics else None,
                'bfd': CanViewBFDSession.message if not user.can_view_bfd_sessions else None,
                'alert_rules': CanViewAlertRule.message if not user.can_view_alert_rules else None,
                'export': CanExportData.message if not user.can_export_data else None,
            }
        }
        return success_response(data, "Permissions IntelliOLT récupérées")

    @action(detail=False, methods=['get'])
    def activity_stats(self, request):
        if not (request.user.is_admin or request.user.is_supervisor):
            return forbidden_response(
                "Accès administrateur requis",
                required_permission="admin ou supervisor"
            )
        days = int(request.query_params.get('days', 7))
        cutoff = timezone.now() - timedelta(days=days)
        activities = UserActivity.objects.filter(created_at__gte=cutoff)
        from django.db.models.functions import TruncDate
        daily_stats = activities.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id'),
            by_action=Count('action'),
            by_severity=Count('severity')
        ).order_by('date')
        # CORRECTION: conversion correcte dictionnaire
        by_action = {
            item['action']: item['count']
            for item in activities.values('action').annotate(count=Count('id'))
        }
        by_severity = {
            item['severity']: item['count']
            for item in activities.values('severity').annotate(count=Count('id'))
        }
        total = activities.count()
        success_rate = activities.filter(success=True).count() / total if total > 0 else 0
        data = {
            'period': f"Derniers {days} jours",
            'total': total,
            'daily': list(daily_stats),
            'by_action': by_action,
            'by_severity': by_severity,
            'success_rate': round(success_rate * 100, 1)
        }
        return success_response(data, "Statistiques d'activité IntelliOLT récupérées")

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def bulk_delete(self, request):
        user_ids = request.data.get('user_ids', [])
        if not user_ids:
            return error_response(
                "Aucun ID utilisateur fourni",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        if request.user.id in user_ids:
            return error_response(
                "Vous ne pouvez pas supprimer votre propre compte",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        deleted_count = User.objects.filter(id__in=user_ids).delete()[0]
        UserActivity.objects.create(
            user=request.user,
            action='delete',
            severity='high',
            description=f"Suppression multiple de {deleted_count} utilisateurs IntelliOLT",
            metadata={'user_ids': user_ids},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        return success_response(
            {'deleted_count': deleted_count},
            f"{deleted_count} utilisateurs IntelliOLT supprimés avec succès"
        )

    @action(detail=False, methods=['get'])
    def not_found_example(self, request):
        user_id = request.query_params.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                serializer = UserMinimalSerializer(user)
                return success_response(serializer.data, "Utilisateur trouvé")
            except User.DoesNotExist:
                return not_found_response(
                    "Utilisateur non trouvé",
                    resource_type="user",
                    resource_id=user_id
                )
        return error_response("ID utilisateur requis", status_code=status.HTTP_400_BAD_REQUEST)


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.select_related('team_lead').prefetch_related('members')
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TeamFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsAdmin]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Team.objects.none()
        if user.is_admin or user.is_supervisor:
            return Team.objects.all()
        return user.teams.all()

    def perform_create(self, serializer):
        team = serializer.save()
        UserActivity.objects.create(
            user=self.request.user,
            action='create',
            description=f"Équipe IntelliOLT {team.name} créée",
            resource_type='team',
            resource_id=str(team.id),
            resource_name=team.name,
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        team = self.get_object()
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return not_found_response("Utilisateur non trouvé", resource_type="user", resource_id=user_id)
        team.members.add(user)
        UserActivity.objects.create(
            user=request.user,
            action='update',
            description=f"{user.email} ajouté à l'équipe IntelliOLT {team.name}",
            resource_type='team',
            resource_id=str(team.id),
            resource_name=team.name,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        return success_response(TeamSerializer(team).data, f"{user.email} ajouté à l'équipe")

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        team = self.get_object()
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return not_found_response("Utilisateur non trouvé", resource_type="user", resource_id=user_id)
        team.members.remove(user)
        UserActivity.objects.create(
            user=request.user,
            action='update',
            description=f"{user.email} retiré de l'équipe IntelliOLT {team.name}",
            resource_type='team',
            resource_id=str(team.id),
            resource_name=team.name,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        return success_response(TeamSerializer(team).data, f"{user.email} retiré de l'équipe")


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    filterset_class = RoleFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def perform_create(self, serializer):
        role = serializer.save()
        UserActivity.objects.create(
            user=self.request.user,
            action='create',
            description=f"Rôle IntelliOLT {role.name} créé",
            resource_type='role',
            resource_id=str(role.id),
            resource_name=role.name,
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PermissionFilter
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['category', 'code', 'name']
    ordering = ['category', 'code']

    @action(detail=False, methods=['get'])
    def grouped(self, request):
        permissions = self.get_queryset()
        grouped = {}
        for category, _ in Permission.CATEGORY_CHOICES:
            perms = permissions.filter(category=category)
            if perms.exists():
                grouped[category] = PermissionSerializer(perms, many=True).data
        return success_response(grouped, "Permissions IntelliOLT groupées par catégorie")


class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserActivity.objects.select_related('user')
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UserActivityFilter
    search_fields = ['description', 'resource_type', 'ip_address']
    ordering_fields = ['created_at', 'severity']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return UserActivity.objects.none()
        if user.is_admin or user.is_supervisor:
            return UserActivity.objects.all()
        return UserActivity.objects.filter(user=user)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        last_24h = timezone.now() - timedelta(hours=24)
        activities = self.get_queryset().filter(created_at__gte=last_24h)[:50]
        serializer = self.get_serializer(activities, many=True)
        return success_response(serializer.data, "Activités IntelliOLT récentes récupérées")

    @action(detail=False, methods=['get'])
    def by_user(self, request):
        if not (request.user.is_admin or request.user.is_supervisor):
            return forbidden_response(
                "Accès administrateur requis",
                required_permission="admin ou supervisor"
            )
        activities = self.get_queryset().values(
            'user__email', 'user__first_name', 'user__last_name', 'user__role'
        ).annotate(
            count=Count('id'),
            last_activity=Max('created_at')
        ).order_by('-count')[:20]
        return success_response(list(activities), "Activités IntelliOLT par utilisateur")

    @action(detail=False, methods=['get'])
    def by_action(self, request):
        if not (request.user.is_admin or request.user.is_supervisor):
            return forbidden_response(
                "Accès administrateur requis",
                required_permission="admin ou supervisor"
            )
        activities = self.get_queryset().values('action').annotate(
            count=Count('id')
        ).order_by('-count')
        return success_response(list(activities), "Activités IntelliOLT par action")