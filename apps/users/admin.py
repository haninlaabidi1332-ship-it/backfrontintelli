# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Team, Permission, Role, UserActivity


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'role_badge', 'status_badge', 'is_active', 'is_verified', 'last_login')
    list_filter = ('role', 'status', 'is_active', 'is_verified', 'two_factor_enabled')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'employee_id')
    ordering = ('email',)
    readonly_fields = ('last_login', 'date_joined', 'failed_login_attempts', 'account_locked_until', 'last_activity_at')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('username', 'first_name', 'last_name', 'phone', 'avatar', 'department', 'job_title', 'employee_id')}),
        ('Permissions', {'fields': ('role', 'status', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Sécurité', {'fields': ('is_verified', 'two_factor_enabled', 'failed_login_attempts', 'account_locked_until', 'last_login_ip')}),
        ('Accès API', {'fields': ('api_access_enabled',)}),
        ('Préférences', {'fields': ('timezone', 'language', 'theme')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined', 'last_activity_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role', 'status'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
    
    def role_badge(self, obj):
        colors = {
            'admin': 'danger',
            'supervisor': 'primary',
            'operator': 'info',
            'viewer': 'secondary',
        }
        color = colors.get(obj.role, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_role_display())
    role_badge.short_description = 'Rôle'
    role_badge.admin_order_field = 'role'
    
    def status_badge(self, obj):
        colors = {
            'active': 'success',
            'inactive': 'secondary',
            'suspended': 'warning',
            'locked': 'danger',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_status_display())
    status_badge.short_description = 'Statut'
    status_badge.admin_order_field = 'status'


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'team_lead', 'member_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    filter_horizontal = ('members',)
    raw_id_fields = ('team_lead',)
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Membres'


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category_badge', 'description')
    list_filter = ('category',)
    search_fields = ('code', 'name', 'description')
    ordering = ('category', 'code')
    
    def category_badge(self, obj):
        colors = {
            'core': 'secondary',
            'users': 'primary',
            'olt': 'info',
            'snmp': 'success',
            'bfd': 'warning',
            'alerting': 'danger',
            'ai_engine': 'dark',
            'analytics': 'primary',
            'eve_ng': 'info',
            'notifications': 'success',
            'admin': 'danger',
        }
        color = colors.get(obj.category, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_category_display())
    category_badge.short_description = 'Catégorie'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'permissions_count', 'description')
    search_fields = ('name', 'description')
    
    def permissions_count(self, obj):
        return len(obj.permissions) if obj.permissions else 0
    permissions_count.short_description = 'Permissions'


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_badge', 'severity_badge', 'description_short', 'created_at', 'success')
    list_filter = ('action', 'severity', 'success', 'created_at')
    search_fields = ('user__email', 'description', 'resource_type')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    def action_badge(self, obj):
        return format_html('<span class="badge bg-secondary">{}</span>', obj.get_action_display())
    action_badge.short_description = 'Action'
    
    def severity_badge(self, obj):
        colors = {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger',
            'critical': 'dark',
        }
        color = colors.get(obj.severity, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_severity_display())
    severity_badge.short_description = 'Sévérité'
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
