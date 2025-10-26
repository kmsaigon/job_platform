from django.contrib import admin
from .models import Job, JobStatusHistory, Application, Message, ApplicationEmail


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


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'application', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'receiver__username', 'subject', 'content')
    readonly_fields = ['created_at']


@admin.register(ApplicationEmail)
class ApplicationEmailAdmin(admin.ModelAdmin):
    list_display = ('application', 'subject', 'sent_by', 'sent_at')
    list_filter = ('sent_at',)
    search_fields = ('application__applicant__username', 'subject', 'message')
    readonly_fields = ['sent_at']
