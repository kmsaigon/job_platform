from django.contrib import admin
from django.http import HttpResponse
import csv
from datetime import datetime
from .models import Job, JobStatusHistory, Application, Message, ApplicationEmail, SavedCandidateSearch


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'status', 'employment_type', 'work_mode', 'posted_by', 'updated_at')
    list_filter = ('status', 'employment_type', 'work_mode', 'company')
    search_fields = ('title', 'company__name')
    readonly_fields = ('slug', 'created_at', 'updated_at', 'published_at', 'unpublished_at')
    actions = ['export_selected_jobs_csv']
    
    def export_selected_jobs_csv(self, request, queryset):
        """Export selected jobs to CSV"""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'jobs_export_{timestamp}.csv'
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow(['Title', 'Company', 'Status', 'Employment Type', 'Work Mode', 
                        'Posted By', 'Location', 'Salary Min', 'Salary Max', 'Currency',
                        'Created At', 'Published At', 'Applications Count'])
        
        for job in queryset.select_related('company', 'posted_by', 'office_location'):
            location = f"{job.office_location.city}, {job.office_location.state}" if job.office_location else ''
            writer.writerow([
                job.title, job.company.name, job.get_status_display(),
                job.get_employment_type_display(), job.get_work_mode_display(),
                job.posted_by.username, location,
                job.salary_min or '', job.salary_max or '', job.currency,
                job.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                job.published_at.strftime('%Y-%m-%d %H:%M:%S') if job.published_at else '',
                job.applications.count()
            ])
        
        return response
    export_selected_jobs_csv.short_description = 'Export selected jobs to CSV'


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
    actions = ['export_selected_applications_csv']
    
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
    
    def export_selected_applications_csv(self, request, queryset):
        """Export selected applications to CSV"""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'applications_export_{timestamp}.csv'
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow(['Applicant', 'Job Title', 'Company', 'Status', 'Applied At', 'Updated At'])
        
        for app in queryset.select_related('job', 'applicant', 'job__company'):
            writer.writerow([
                app.applicant.username, app.job.title, app.job.company.name,
                app.get_status_display(),
                app.applied_at.strftime('%Y-%m-%d %H:%M:%S'),
                app.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    export_selected_applications_csv.short_description = 'Export selected applications to CSV'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'application', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'receiver__username', 'subject', 'content')
    readonly_fields = ['created_at']
    actions = ['export_selected_messages_csv']
    
    def export_selected_messages_csv(self, request, queryset):
        """Export selected messages to CSV"""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'messages_export_{timestamp}.csv'
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        writer.writerow(['Sender', 'Receiver', 'Job', 'Subject', 'Is Read', 'Created At'])
        
        for msg in queryset.select_related('sender', 'receiver', 'application', 'application__job'):
            job_title = msg.application.job.title if msg.application else ''
            writer.writerow([
                msg.sender.username, msg.receiver.username, job_title,
                msg.subject, msg.is_read,
                msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    export_selected_messages_csv.short_description = 'Export selected messages to CSV'


@admin.register(ApplicationEmail)
class ApplicationEmailAdmin(admin.ModelAdmin):
    list_display = ('application', 'subject', 'sent_by', 'sent_at')
    list_filter = ('sent_at',)
    search_fields = ('application__applicant__username', 'subject', 'message')
    readonly_fields = ['sent_at']


@admin.register(SavedCandidateSearch)
class SavedCandidateSearchAdmin(admin.ModelAdmin):
    list_display = ('name', 'recruiter', 'notifications_enabled', 'last_checked_at', 'last_notified_at', 'created_at')
    list_filter = ('notifications_enabled', 'created_at', 'last_checked_at')
    search_fields = ('name', 'recruiter__username', 'recruiter__email', 'skills', 'location')
    readonly_fields = ['created_at', 'updated_at', 'last_checked_at', 'last_notified_at']
    
    fieldsets = (
        ('Search Info', {
            'fields': ('recruiter', 'name')
        }),
        ('Search Criteria', {
            'fields': ('skills', 'location', 'experience', 'search_lat', 'search_lng', 'distance_radius', 'sort_by')
        }),
        ('Notifications', {
            'fields': ('notifications_enabled', 'last_checked_at', 'last_notified_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
