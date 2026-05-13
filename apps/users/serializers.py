# apps/users/serializers.py
"""
Sérialiseurs pour l'application Utilisateurs IntelliOLT – AI-Powered Fiber Network Supervision Platform
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Team, Role, Permission, UserActivity


class UserMinimalSerializer(serializers.ModelSerializer):
    """Sérialiseur minimal pour les listes"""
    full_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    role_icon = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 
            'role', 'role_display', 'role_icon', 'avatar'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_role_icon(self, obj):
        icons = {
            'admin': '👑',
            'supervisor': '📊',
            'operator': '🖥️',
            'viewer': '👁️',
        }
        return icons.get(obj.role, '👤')


class TeamSerializer(serializers.ModelSerializer):
    """Sérialiseur pour Team"""
    team_lead_name = serializers.CharField(source='team_lead.get_full_name', read_only=True)
    team_lead_email = serializers.EmailField(source='team_lead.email', read_only=True)
    members_count = serializers.SerializerMethodField()
    members_list = UserMinimalSerializer(source='members', many=True, read_only=True)
    
    class Meta:
        model = Team
        fields = [
            'id', 'name', 'description', 'team_lead', 'team_lead_name',
            'team_lead_email', 'members', 'members_count', 'members_list',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_members_count(self, obj):
        return obj.members.count()


class PermissionSerializer(serializers.ModelSerializer):
    """Sérialiseur pour Permission"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Permission
        fields = [
            'id', 'code', 'name', 'description', 
            'category', 'category_display', 'created_at'
        ]
        read_only_fields = ['created_at']


class RoleSerializer(serializers.ModelSerializer):
    """Sérialiseur pour Role"""
    permissions_details = serializers.SerializerMethodField()
    permissions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'description', 'permissions',
            'permissions_count', 'permissions_details', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_permissions_details(self, obj):
        perms = Permission.objects.filter(code__in=obj.permissions)
        return PermissionSerializer(perms, many=True).data
    
    def get_permissions_count(self, obj):
        return len(obj.permissions) if obj.permissions else 0


class UserActivitySerializer(serializers.ModelSerializer):
    """Sérialiseur pour UserActivity"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    time_ago = serializers.SerializerMethodField()
    severity_icon = serializers.SerializerMethodField()
    
    class Meta:
        model = UserActivity
        fields = '__all__'
        read_only_fields = ['created_at']
    
    def get_time_ago(self, obj):
        from apps.core.utils import format_timesince
        return format_timesince(obj.created_at, default="à l'instant")
    
    def get_severity_icon(self, obj):
        icons = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴',
        }
        return icons.get(obj.severity, '⚪')


class UserListSerializer(serializers.ModelSerializer):
    """Sérialiseur pour liste d'utilisateurs (IntelliOLT)"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_admin = serializers.BooleanField(read_only=True)
    role_icon = serializers.SerializerMethodField()
    status_badge = serializers.SerializerMethodField()
    
    # Permissions métier IntelliOLT
    can_view_olt = serializers.BooleanField(read_only=True)
    can_manage_olt = serializers.BooleanField(read_only=True)
    can_view_ont = serializers.BooleanField(read_only=True)
    can_manage_ont = serializers.BooleanField(read_only=True)
    can_view_snmp_metrics = serializers.BooleanField(read_only=True)
    can_manage_snmp_oids = serializers.BooleanField(read_only=True)
    can_view_bfd_sessions = serializers.BooleanField(read_only=True)
    can_manage_bfd_sessions = serializers.BooleanField(read_only=True)
    can_view_alert_rules = serializers.BooleanField(read_only=True)
    can_manage_alert_rules = serializers.BooleanField(read_only=True)
    can_view_alerts = serializers.BooleanField(read_only=True)
    can_acknowledge_alert = serializers.BooleanField(read_only=True)
    can_resolve_alert = serializers.BooleanField(read_only=True)
    can_view_anomalies = serializers.BooleanField(read_only=True)
    can_manage_ml_models = serializers.BooleanField(read_only=True)
    can_view_dashboard = serializers.BooleanField(read_only=True)
    can_export_data = serializers.BooleanField(read_only=True)
    can_manage_labs = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_display', 'role_icon',
            'status', 'status_display', 'status_badge',
            'department', 'job_title', 'is_active', 'is_admin',
            'can_view_olt', 'can_manage_olt',
            'can_view_ont', 'can_manage_ont',
            'can_view_snmp_metrics', 'can_manage_snmp_oids',
            'can_view_bfd_sessions', 'can_manage_bfd_sessions',
            'can_view_alert_rules', 'can_manage_alert_rules',
            'can_view_alerts', 'can_acknowledge_alert', 'can_resolve_alert',
            'can_view_anomalies', 'can_manage_ml_models',
            'can_view_dashboard', 'can_export_data', 'can_manage_labs',
            'last_login', 'last_activity_at', 'created_at'
        ]
        read_only_fields = ['last_login', 'last_activity_at', 'created_at']
    
    def get_role_icon(self, obj):
        icons = {
            'admin': '👑',
            'supervisor': '📊',
            'operator': '🖥️',
            'viewer': '👁️',
        }
        return icons.get(obj.role, '👤')
    
    def get_status_badge(self, obj):
        badges = {
            'active': '✅',
            'inactive': '⏸️',
            'suspended': '🚫',
            'locked': '🔒',
        }
        return badges.get(obj.status, '❓')


class UserDetailSerializer(serializers.ModelSerializer):
    """Sérialiseur détaillé pour User (IntelliOLT)"""
    teams = TeamSerializer(many=True, read_only=True)
    recent_activities = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    # Toutes les permissions métier
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        exclude = ['password']
        read_only_fields = [
            'last_login', 'date_joined', 'created_at', 'updated_at',
            'failed_login_attempts', 'account_locked_until'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_recent_activities(self, obj):
        activities = obj.activities.all()[:10]
        return UserActivitySerializer(activities, many=True).data
    
    def get_permissions(self, obj):
        """Retourne toutes les permissions métier IntelliOLT"""
        return {
            # OLT & équipements
            'can_view_olt': obj.can_view_olt,
            'can_manage_olt': obj.can_manage_olt,
            'can_view_ont': obj.can_view_ont,
            'can_manage_ont': obj.can_manage_ont,
            
            # SNMP
            'can_view_snmp_metrics': obj.can_view_snmp_metrics,
            'can_manage_snmp_oids': obj.can_manage_snmp_oids,
            
            # BFD
            'can_view_bfd_sessions': obj.can_view_bfd_sessions,
            'can_manage_bfd_sessions': obj.can_manage_bfd_sessions,
            
            # Alertes
            'can_view_alert_rules': obj.can_view_alert_rules,
            'can_manage_alert_rules': obj.can_manage_alert_rules,
            'can_view_alerts': obj.can_view_alerts,
            'can_acknowledge_alert': obj.can_acknowledge_alert,
            'can_resolve_alert': obj.can_resolve_alert,
            
            # IA / ML
            'can_view_anomalies': obj.can_view_anomalies,
            'can_manage_ml_models': obj.can_manage_ml_models,
            
            # Dashboard & exports
            'can_view_dashboard': obj.can_view_dashboard,
            'can_export_data': obj.can_export_data,
            
            # EVE-NG
            'can_manage_labs': obj.can_manage_labs,
            
            # Notifications
            'can_view_notifications': obj.can_view_notifications,
            'can_manage_notifications': obj.can_manage_notifications,
        }


class UserCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour création d'utilisateur"""
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'role', 'department', 
            'job_title', 'phone', 'employee_id'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Les mots de passe ne correspondent pas",
                "password_confirm": "Les mots de passe ne correspondent pas"
            })
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        validated_data.setdefault('is_active', True)
        validated_data.setdefault('status', 'active')
        validated_data.setdefault('api_access_enabled', True)
        
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour mise à jour utilisateur"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'role', 'department',
            'job_title', 'phone', 'avatar', 'timezone', 'language', 'theme',
            'status', 'api_access_enabled'
        ]
    
    def validate_role(self, value):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # Seul admin peut changer le rôle
            if not request.user.is_admin:
                if request.user.role != value:
                    raise serializers.ValidationError(
                        "Vous n'avez pas la permission de changer le rôle"
                    )
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Sérialiseur pour changement de mot de passe"""
    old_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Ancien mot de passe incorrect")
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "Les nouveaux mots de passe ne correspondent pas",
                "new_password_confirm": "Les nouveaux mots de passe ne correspondent pas"
            })
        return attrs


class UserStatsSerializer(serializers.Serializer):
    """Statistiques utilisateur pour IntelliOLT"""
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    inactive_users = serializers.IntegerField()
    by_role = serializers.DictField()
    recent_activities = serializers.IntegerField()
    api_users = serializers.IntegerField()
    
    # Statistiques par rôle
    admins = serializers.IntegerField()
    supervisors = serializers.IntegerField()
    operators = serializers.IntegerField()
    viewers = serializers.IntegerField()


class UserActivityStatsSerializer(serializers.Serializer):
    """Statistiques d'activité IntelliOLT"""
    date = serializers.DateField()
    count = serializers.IntegerField()
    by_action = serializers.DictField()
    by_severity = serializers.DictField()