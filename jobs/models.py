from django.conf import settings
from django.db import models
from django.utils.text import slugify
from companies.models import Company, OfficeLocation
from .manager import JobManager


class Job(models.Model):
    objects = JobManager()
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        CLOSED = 'closed', 'Closed'

    class EmploymentType(models.TextChoices):
        FULL_TIME = 'full_time', 'Full-time'
        PART_TIME = 'part_time', 'Part-time'
        CONTRACT = 'contract', 'Contract'
        INTERNSHIP = 'internship', 'Internship'
        TEMPORARY = 'temporary', 'Temporary'
        OTHER = 'other', 'Other'

    class WorkMode(models.TextChoices):
        REMOTE = 'remote', 'Remote'
        HYBRID = 'hybrid', 'Hybrid'
        ON_SITE = 'on_site', 'On-site'

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='jobs')
    title = models.CharField(max_length=255)
    description = models.TextField()
    required_skills = models.TextField(blank=True, help_text='Required skills (one per line or comma-separated)')
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices)
    work_mode = models.CharField(max_length=20, choices=WorkMode.choices)
    visa_required = models.BooleanField(default=False)
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    office_location = models.ForeignKey(OfficeLocation, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='posted_jobs')
    published_at = models.DateTimeField(null=True, blank=True)
    unpublished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
                raise models.ValidationError('Minimum salary cannot exceed maximum salary.')

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:60] or 'job'
            self.slug = f"{base}-{self.pk or ''}".strip('-')
        super().save(*args, **kwargs)
        # Ensure slug includes ID for uniqueness and stability
        slug_with_id = f"{slugify(self.title)[:60] or 'job'}-{self.pk}"
        if self.slug != slug_with_id:
            self.slug = slug_with_id
            super().save(update_fields=['slug'])

    def __str__(self) -> str:
        return f"{self.title} @ {self.company.name}"


class JobStatusHistory(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='status_history')
    from_status = models.CharField(max_length=12, choices=Job.Status.choices, null=True, blank=True)
    to_status = models.CharField(max_length=12, choices=Job.Status.choices)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-changed_at']


class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = 'applied', 'Applied'
        REVIEW = 'review', 'Under Review'
        INTERVIEW = 'interview', 'Interview'
        OFFER = 'offer', 'Offer'
        REJECTED = 'rejected', 'Rejected'
        WITHDRAWN = 'withdrawn', 'Withdrawn'
        CLOSED = 'closed', 'Closed'

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    application_note = models.TextField(help_text='Tell the employer why you are a good fit for this role')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPLIED)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']
        unique_together = ['job', 'applicant']  # Prevent duplicate applications

    def __str__(self):
        return f"{self.applicant.username} -> {self.job.title}"


class Message(models.Model):
    """In-platform messaging between recruiters and candidates"""
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"


class ApplicationEmail(models.Model):
    """Track emails sent through the platform"""
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='sent_emails')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_application_emails')
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Email for {self.application}"


class SavedCandidateSearch(models.Model):
    """Saved candidate searches for recruiters with notification support"""
    recruiter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_candidate_searches')
    name = models.CharField(max_length=200, help_text='A descriptive name for this search')
    
    # Search parameters
    skills = models.CharField(max_length=500, blank=True)
    location = models.CharField(max_length=200, blank=True)
    experience = models.CharField(max_length=500, blank=True)
    search_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    search_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    distance_radius = models.CharField(max_length=10, blank=True)
    sort_by = models.CharField(max_length=20, default='skills_match')
    
    # Notification settings
    notifications_enabled = models.BooleanField(default=True, help_text='Get notified when new candidates match this search')
    last_checked_at = models.DateTimeField(null=True, blank=True, help_text='Last time this search was checked for new matches')
    last_notified_at = models.DateTimeField(null=True, blank=True, help_text='Last time a notification was sent for this search')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name_plural = 'Saved Candidate Searches'
    
    def __str__(self):
        return f"{self.name} ({self.recruiter.username})"
