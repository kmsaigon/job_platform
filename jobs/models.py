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
