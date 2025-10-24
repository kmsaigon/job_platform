from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.conf import settings
from .forms import JobForm, JobSearchForm, ApplicationForm
from .models import Job, JobStatusHistory, Application
from companies.models import OfficeLocation

def is_admin(user):
    return user.is_superuser or user.groups.filter(name='admin').exists()


def is_recruiter(user):
    return user.groups.filter(name='recruiter').exists()


def is_job_seeker(user):
    # Job seeker is any authenticated user who is NOT a recruiter
    return user.is_authenticated and not is_recruiter(user) and not is_admin(user)


class JobPublicListView(ListView):
    model = Job
    template_name = 'jobs/public_list.html'
    context_object_name = 'jobs'

    def get_queryset(self):
        return Job.objects.filter(status=Job.Status.PUBLISHED).select_related('company')\
            .order_by('-published_at', '-updated_at')


class JobPublicDetailView(DetailView):
    model = Job
    template_name = 'jobs/public_detail.html'
    context_object_name = 'job'

    def get_queryset(self):
        qs = Job.objects.select_related('company', 'office_location')
        if self.request.user.is_authenticated and (is_admin(self.request.user)):
            return qs
        return qs.filter(status=Job.Status.PUBLISHED)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if user has already applied
        if self.request.user.is_authenticated:
            context['has_applied'] = Application.objects.filter(
                job=self.object,
                applicant=self.request.user
            ).exists()
            if context['has_applied']:
                context['user_application'] = Application.objects.get(
                    job=self.object,
                    applicant=self.request.user
                )
        return context


class OwnerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        obj = getattr(self, 'object', None)
        if obj is None:
            return True
        return obj.posted_by_id == self.request.user.id or is_admin(self.request.user)


class RecruiterRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_admin(self.request.user) or is_recruiter(self.request.user)


class JobMyListView(LoginRequiredMixin, RecruiterRequiredMixin, ListView):
    model = Job
    template_name = 'jobs/my_list.html'
    context_object_name = 'jobs'

    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user).select_related('company')\
            .order_by('-updated_at')


class JobCreateView(LoginRequiredMixin, RecruiterRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'
    success_url = reverse_lazy('jobs:my_list')

    def form_valid(self, form):
        form.instance.posted_by = self.request.user
        messages.success(self.request, 'Job created (Draft).')
        return super().form_valid(form)


class JobUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'
    success_url = reverse_lazy('jobs:my_list')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        self.object = obj
        return obj


@login_required
@user_passes_test(lambda u: is_admin(u) or is_recruiter(u))
def job_publish(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if job.posted_by_id != request.user.id and not is_admin(request.user):
        return HttpResponseForbidden()
    old = job.status
    if job.status != Job.Status.PUBLISHED:
        job.status = Job.Status.PUBLISHED
        job.published_at = timezone.now()
        job.unpublished_at = None
        job.save(update_fields=['status', 'published_at', 'unpublished_at'])
        JobStatusHistory.objects.create(job=job, from_status=old, to_status=job.status, changed_by=request.user)
        messages.success(request, 'Job published.')
    return redirect('jobs:my_list')


@login_required
@user_passes_test(lambda u: is_admin(u) or is_recruiter(u))
def job_unpublish(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if job.posted_by_id != request.user.id and not is_admin(request.user):
        return HttpResponseForbidden()
    old = job.status
    if job.status != Job.Status.DRAFT:
        job.status = Job.Status.DRAFT
        job.unpublished_at = timezone.now()
        job.save(update_fields=['status', 'unpublished_at'])
        JobStatusHistory.objects.create(job=job, from_status=old, to_status=job.status, changed_by=request.user)
        messages.info(request, 'Job unpublished (Draft).')
    return redirect('jobs:my_list')


@login_required
@user_passes_test(lambda u: is_admin(u) or is_recruiter(u))
def job_close(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if job.posted_by_id != request.user.id and not is_admin(request.user):
        return HttpResponseForbidden()
    old = job.status
    if job.status != Job.Status.CLOSED:
        job.status = Job.Status.CLOSED
        job.save(update_fields=['status'])
        JobStatusHistory.objects.create(job=job, from_status=old, to_status=job.status, changed_by=request.user)
        
        applications_closed = Application.objects.filter(job=job).exclude(status=Application.Status.CLOSED)
        for application in applications_closed:
            application.status = Application.Status.CLOSED
            application.save()

        messages.info(request, f'Job closed and {applications_closed.count()} applications marked as closed.')
    return redirect('jobs:my_list')


class JobSearchView(ListView):
    model = Job
    template_name = 'jobs/public_list.html'
    context_object_name = 'jobs'
    paginate_by = 20
    
    def get_queryset(self):
        # Start with published jobs only
        queryset = Job.objects.filter(status=Job.Status.PUBLISHED).select_related('company', 'office_location').order_by('-published_at', '-updated_at')
        
        # Get form data
        form = JobSearchForm(self.request.GET)
        
        if form.is_valid():
            cleaned_data = form.cleaned_data
            
            # Title search (search in title, description, and company name)
            if cleaned_data.get('title'):
                title_query = cleaned_data['title']
                queryset = queryset.filter(
                    Q(title__icontains=title_query) |
                    Q(description__icontains=title_query) |
                    Q(company__name__icontains=title_query)
                )
            
            # Location search (search in office location fields)
            if cleaned_data.get('location'):
                location_query = cleaned_data['location']
                queryset = queryset.filter(
                    Q(office_location__city__icontains=location_query) |
                    Q(office_location__state__icontains=location_query) |
                    Q(office_location__country__icontains=location_query) |
                    Q(office_location__address__icontains=location_query)
                ).distinct()
            
            # Salary range
            if cleaned_data.get('salary_min'):
                queryset = queryset.filter(
                    Q(salary_max__gte=cleaned_data['salary_min']) | 
                    Q(salary_max__isnull=True)
                )
            
            if cleaned_data.get('salary_max'):
                queryset = queryset.filter(
                    Q(salary_min__lte=cleaned_data['salary_max']) | 
                    Q(salary_min__isnull=True)
                )
            
            # Work mode filter
            if cleaned_data.get('work_mode'):
                queryset = queryset.filter(work_mode=cleaned_data['work_mode'])
            
            # Employment type filter (multiple selection)
            if cleaned_data.get('employment_type'):
                queryset = queryset.filter(employment_type__in=cleaned_data['employment_type'])
            
            # Visa required filter
            if cleaned_data.get('visa_required'):
                queryset = queryset.filter(visa_required=True)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = JobSearchForm(self.request.GET)
        context['form'] = form
        context['total_jobs'] = self.get_queryset().count()
        
        # Get user's applications for showing applied status
        if self.request.user.is_authenticated:
            user_applications = Application.objects.filter(
                applicant=self.request.user
            ).values_list('job_id', flat=True)
            context['user_applications'] = list(user_applications)
        else:
            context['user_applications'] = []
        
        # Active filters for display
        if form.is_valid():
            active_filters = {}
            for field_name, value in form.cleaned_data.items():
                if value:
                    if field_name == 'employment_type' and isinstance(value, list):
                        active_filters[field_name] = ', '.join(value)
                    elif field_name in ['salary_min', 'salary_max'] and value:
                        active_filters[field_name] = f"${value:,.0f}"
                    elif value not in [None, '', [], False]:
                        active_filters[field_name] = str(value)
            context['active_filters'] = active_filters
        
        return context


# Application Views
@login_required
def apply_to_job(request, pk):
    """Handle job application submission"""
    job = get_object_or_404(Job, pk=pk, status=Job.Status.PUBLISHED)
    
    # Prevent recruiters from applying
    if is_recruiter(request.user) or is_admin(request.user):
        messages.error(request, 'Recruiters cannot apply to jobs.')
        return redirect('jobs:public_detail', pk=job.pk, slug=job.slug)
    
    # Check if already applied
    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.info(request, 'You have already applied to this job.')
        return redirect('jobs:public_detail', pk=job.pk, slug=job.slug)
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()
            messages.success(request, 'Application submitted successfully!')
            return redirect('jobs:public_detail', pk=job.pk, slug=job.slug)
    else:
        form = ApplicationForm()
    
    context = {
        'job': job,
        'form': form
    }
    return render(request, 'jobs/apply.html', context)


@login_required
def my_applications(request):
    """View all applications by the current user"""
    if is_recruiter(request.user) or is_admin(request.user):
        messages.error(request, 'This page is for job seekers only.')
        return redirect('jobs:public_list')
    
    applications = Application.objects.filter(
        applicant=request.user
    ).select_related('job', 'job__company').order_by('-applied_at')
    
    context = {
        'applications': applications
    }
    return render(request, 'jobs/my_applications.html', context)

@login_required
def withdraw_application(request, application_id):
    """Allow job seekers to withdraw their application"""
    application = get_object_or_404(Application, id=application_id)

    if application.applicant != request.user:
        return HttpResponseForbidden("You cannot withdraw this application.")
    
    if application.status not in ['applied', 'review']:
        messages.error(request, 'You can only withdraw applications that are in "Applied" or "Under Review" status.')
        return redirect('jobs:my_applications')
    
    application.status = Application.Status.WITHDRAWN
    application.save()

    messages.success(request, f'Your application for "{application.job.title}" has been withdrawn.')
    return redirect('jobs:my_applications')


@login_required
def job_map(request):
    """
    Display an interactive map showing job postings by office location.
    """
    # Get all office locations with coordinates that have published jobs
    office_locations = OfficeLocation.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
        job__status=Job.Status.PUBLISHED
    ).annotate(
        job_count=Count('job', filter=Q(job__status=Job.Status.PUBLISHED))
    ).select_related('company').distinct()
    
    # Prepare data for JavaScript
    office_data = []
    for office in office_locations:
        # Get all published jobs at this office
        jobs_at_office = Job.objects.filter(
            office_location=office,
            status=Job.Status.PUBLISHED
        ).select_related('company')
        
        # Check if user has applied to any jobs at this office
        user_applications = []
        if request.user.is_authenticated:
            user_applications = Application.objects.filter(
                job__in=jobs_at_office,
                applicant=request.user
            ).values_list('job_id', flat=True)
        
        office_data.append({
            'id': office.id,
            'company_name': office.company.name,
            'address': office.address,
            'city': office.city,
            'state': office.state,
            'country': office.country,
            'latitude': float(office.latitude),
            'longitude': float(office.longitude),
            'job_count': office.job_count,
            'jobs': [
                {
                    'id': job.id,
                    'title': job.title,
                    'employment_type': job.get_employment_type_display(),
                    'work_mode': job.get_work_mode_display(),
                    'salary_min': float(job.salary_min) if job.salary_min else None,
                    'salary_max': float(job.salary_max) if job.salary_max else None,
                    'currency': job.currency,
                    'slug': job.slug,
                    'has_applied': job.id in user_applications,
                    'url': reverse('jobs:public_detail', kwargs={'pk': job.pk, 'slug': job.slug})
                }
                for job in jobs_at_office
            ]
        })
    
    context = {
        'template_data': {
            'title': 'Jobs Map',
            'office_data': office_data,
            'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
        }
    }
    
    return render(request, 'jobs/job_map.html', context)
