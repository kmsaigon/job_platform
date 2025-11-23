from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

User = get_user_model()

# Unregister the default User admin if it's already registered
if admin.site.is_registered(User):
    admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Enhanced UserAdmin with bulk actions and better display"""
    
    list_display = ('username', 'email', 'display_groups', 'display_profile', 'is_active', 'is_superuser', 'user_stats', 'date_joined')
    list_filter = ('is_active', 'is_superuser', 'is_staff', 'groups', 'date_joined')
    search_fields = ('username', 'email', 'profile__name')
    actions = ['assign_group_recruiter', 'assign_group_job_seeker', 'assign_group_admin', 
               'remove_group_recruiter', 'remove_group_job_seeker', 'remove_group_admin',
               'activate_users', 'deactivate_users', 'make_superuser', 'remove_superuser']
    
    # BaseUserAdmin already includes 'groups' in its fieldsets, so we don't need to add it again
    # We can customize fieldsets if needed, but for now we'll use the base ones
    
    def display_groups(self, obj):
        """Display user groups as badges"""
        groups = obj.groups.all()
        if not groups and not obj.is_superuser:
            return format_html('<span class="badge bg-secondary">No Group</span>')
        
        badges = []
        if obj.is_superuser:
            badges.append('<span class="badge bg-danger">Superuser</span>')
        for group in groups:
            color = 'primary' if group.name == 'admin' else 'info' if group.name == 'recruiter' else 'success'
            badges.append(f'<span class="badge bg-{color}">{group.name}</span>')
        return mark_safe(' '.join(badges))
    display_groups.short_description = 'Groups/Roles'
    
    def display_profile(self, obj):
        """Display link to profile if exists"""
        if hasattr(obj, 'profile'):
            url = reverse('admin:profiles_profile_change', args=[obj.profile.pk])
            return format_html('<a href="{}">{}</a>', url, obj.profile.name)
        return format_html('<span class="text-muted">No Profile</span>')
    display_profile.short_description = 'Profile'
    
    def user_stats(self, obj):
        """Display user statistics"""
        jobs_count = obj.posted_jobs.count()
        applications_count = obj.applications.count()
        stats = []
        if jobs_count > 0:
            stats.append(f'{jobs_count} job(s)')
        if applications_count > 0:
            stats.append(f'{applications_count} application(s)')
        return ', '.join(stats) if stats else '—'
    user_stats.short_description = 'Stats'
    
    # Bulk Actions
    def assign_group_recruiter(self, request, queryset):
        """Assign recruiter group to selected users"""
        group, _ = Group.objects.get_or_create(name='recruiter')
        count = 0
        for user in queryset:
            if not user.groups.filter(name='recruiter').exists():
                user.groups.add(group)
                count += 1
        self.message_user(request, f'Successfully assigned recruiter group to {count} user(s).')
    assign_group_recruiter.short_description = 'Assign recruiter group'
    
    def assign_group_job_seeker(self, request, queryset):
        """Assign job_seeker group to selected users"""
        group, _ = Group.objects.get_or_create(name='job_seeker')
        count = 0
        for user in queryset:
            if not user.groups.filter(name='job_seeker').exists():
                user.groups.add(group)
                count += 1
        self.message_user(request, f'Successfully assigned job_seeker group to {count} user(s).')
    assign_group_job_seeker.short_description = 'Assign job_seeker group'
    
    def assign_group_admin(self, request, queryset):
        """Assign admin group to selected users"""
        group, _ = Group.objects.get_or_create(name='admin')
        count = 0
        for user in queryset:
            if not user.groups.filter(name='admin').exists():
                user.groups.add(group)
                count += 1
        self.message_user(request, f'Successfully assigned admin group to {count} user(s).')
    assign_group_admin.short_description = 'Assign admin group'
    
    def remove_group_recruiter(self, request, queryset):
        """Remove recruiter group from selected users"""
        try:
            group = Group.objects.get(name='recruiter')
            count = queryset.filter(groups=group).count()
            for user in queryset:
                user.groups.remove(group)
            self.message_user(request, f'Successfully removed recruiter group from {count} user(s).')
        except Group.DoesNotExist:
            self.message_user(request, 'Recruiter group does not exist.', level='warning')
    remove_group_recruiter.short_description = 'Remove recruiter group'
    
    def remove_group_job_seeker(self, request, queryset):
        """Remove job_seeker group from selected users"""
        try:
            group = Group.objects.get(name='job_seeker')
            count = queryset.filter(groups=group).count()
            for user in queryset:
                user.groups.remove(group)
            self.message_user(request, f'Successfully removed job_seeker group from {count} user(s).')
        except Group.DoesNotExist:
            self.message_user(request, 'Job seeker group does not exist.', level='warning')
    remove_group_job_seeker.short_description = 'Remove job_seeker group'
    
    def remove_group_admin(self, request, queryset):
        """Remove admin group from selected users"""
        try:
            group = Group.objects.get(name='admin')
            count = queryset.filter(groups=group).count()
            for user in queryset:
                user.groups.remove(group)
            self.message_user(request, f'Successfully removed admin group from {count} user(s).')
        except Group.DoesNotExist:
            self.message_user(request, 'Admin group does not exist.', level='warning')
    remove_group_admin.short_description = 'Remove admin group'
    
    def activate_users(self, request, queryset):
        """Activate selected users"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'Successfully activated {count} user(s).')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'Successfully deactivated {count} user(s).')
    deactivate_users.short_description = 'Deactivate selected users'
    
    def make_superuser(self, request, queryset):
        """Make selected users superusers"""
        count = queryset.update(is_superuser=True, is_staff=True)
        self.message_user(request, f'Successfully made {count} user(s) superuser(s).')
    make_superuser.short_description = 'Make superuser'
    
    def remove_superuser(self, request, queryset):
        """Remove superuser status from selected users"""
        count = queryset.update(is_superuser=False)
        self.message_user(request, f'Successfully removed superuser status from {count} user(s).')
    remove_superuser.short_description = 'Remove superuser status'

