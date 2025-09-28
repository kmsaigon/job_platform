from django.contrib import admin
from .models import Job, JobStatusHistory, Application


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'status', 'employment_type', 'work_mode', 'posted_by', 'updated_at')
    list_filter = ('status', 'employment_type', 'work_mode', 'company')
    search_fields = ('title', 'company__name')
    readonly_fields = ('slug', 'created_at', 'updated_at', 'published_at', 'unpublished_at')


@admin.register(JobStatusHistory)
class JobStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('job', 'from_status', 'to_status', 'changed_by', 'changed_at')
    list_filter = ('to_status',) # yo, gurt


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'job', 'status', 'applied_at']
    list_filter = ['status', 'applied_at']
    search_fields = ['applicant__username', 'applicant__email', 'job__title', 'application_note']
    readonly_fields = ['applied_at', 'updated_at']
    
    fieldsets = (
        ('Application Info', {
            'fields': ('job', 'applicant', 'status')
        }),
        ('Application Note', {
            'fields': ('application_note',)
        }),
        ('Timestamps', {
            'fields': ('applied_at', 'updated_at')
        }),
    ) # yo, gurt
