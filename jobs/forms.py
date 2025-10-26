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
import json
from .forms import JobForm, JobSearchForm, ApplicationForm, CandidateSearchForm, MessageForm, ApplicationEmailForm
from .models import Job, JobStatusHistory, Application, Message, ApplicationEmail
from profiles.models import Profile
from companies.models import OfficeLocation
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from math import radians, sin, cos, sqrt, atan2
from .models import Job


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


def haversine(lat1, lon1, lat2, lon2):
    """Calculate the distance (miles) between two lat/lon points."""
    R = 3958.8  # Radius of Earth in miles
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


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
                    Q(office_location__country__icontains=location_query)
                )
            
            # Work style filter
            if cleaned_data.get('work_mode'):
                queryset = queryset.filter(work_mode=cleaned_data['work_mode'])
            
            # Employment type filter (multiple selection)
            employment_types = cleaned_data.get('employment_type')
            if employment_types:
                queryset = queryset.filter(employment_type__in=employment_types)
            
            # Salary range filters
            if cleaned_data.get('salary_min'):
                queryset = queryset.filter(salary_min__gte=cleaned_data['salary_min'])
            
            if cleaned_data.get('salary_max'):
                queryset = queryset.filter(salary_max__lte=cleaned_data['salary_max'])
            
            # Visa required filter
            if cleaned_data.get('visa_required') is not None:
                queryset = queryset.filter(visa_required=cleaned_data['visa_required'])
            
            # NEW: Commute radius filter
            commute_lat = cleaned_data.get('commute_lat')
            commute_lng = cleaned_data.get('commute_lng')
            commute_radius = cleaned_data.get('commute_radius')
            
            if commute_lat and commute_lng and commute_radius:
                try:
                    user_lat = float(commute_lat)
                    user_lng = float(commute_lng)
                    radius = float(commute_radius)
                    
                    # Filter jobs within radius
                    filtered_jobs = []
                    for job in queryset:
                        # Include remote jobs regardless of distance
                        if job.work_mode == Job.WorkMode.REMOTE:
                            filtered_jobs.append(job.id)
                        # Check distance for jobs with office locations
                        elif job.office_location and job.office_location.latitude and job.office_location.longitude:
                            distance = haversine(
                                user_lat, user_lng,
                                float(job.office_location.latitude),
                                float(job.office_location.longitude)
                            )
                            if distance <= radius:
                                filtered_jobs.append(job.id)
                    
                    queryset = queryset.filter(id__in=filtered_jobs)
                except (ValueError, TypeError):
                    pass  # Invalid coordinates, skip filter
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = JobSearchForm(self.request.GET)
        context['GOOGLE_MAPS_API_KEY'] = settings.GOOGLE_MAPS_API_KEY
        
        # Add active filters to context for display
        form = JobSearchForm(self.request.GET)
        if form.is_valid():
            active_filters = {}
            for field_name, value in form.cleaned_data.items():
                if value:
                    if isinstance(value, list):
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
def recommendations(request):
    """Show job recommendations based on user skills"""
    if not hasattr(request.user, 'profile') or not request.user.profile.skills:
        messages.warning(request, 'Please update your profile with skills to receive personalized job recommendations.')
        return redirect('profiles:profiles.edit')
    
    user_skills = request.user.profile.skills
    # Parse user skills - handle both comma-separated and line-separated
    user_skills_list = []
    for line in user_skills.replace(',', '\n').split('\n'):
        for skill in line.split(','):
            skill = skill.strip().lower()
            if skill:
                user_skills_list.append(skill)
    
    if not user_skills_list:
        messages.warning(request, 'Please add skills to your profile to receive recommendations.')
        return redirect('profiles:profiles.edit')
    
    # Get all published jobs
    all_jobs = Job.objects.filter(status=Job.Status.PUBLISHED).select_related('company', 'office_location')
    
    # Calculate skill match score for each job
    recommended_jobs = []
    processed_jobs = {}  # Keep track of jobs and their match scores
    
    for job in all_jobs:
        # Skip if we've already processed this job
        if job.id in processed_jobs:
            continue
            
        skill_matches = set()  # Use a set to avoid duplicate skill matches
        job_skills_list = []
        
        # Check skills in required_skills field
        if job.required_skills:
            for line in job.required_skills.replace(',', '\n').split('\n'):
                for skill in line.split(','):
                    skill = skill.strip().lower()
                    if skill:
                        job_skills_list.append(skill)
                        if skill in user_skills_list:
                            skill_matches.add(skill)
        
        # Check skills in job description
        if job.description:
            for user_skill in user_skills_list:
                user_skill_lower = user_skill.lower()
                if user_skill_lower in job.description.lower():
                    skill_matches.add(user_skill)
        
        match_count = len(skill_matches)
        total_required = max(len(job_skills_list), 1)  # Ensure we don't divide by zero
        match_score = (match_count / total_required) * 100 if total_required > 0 else 0
        
        # Include job if there's at least one skill match in either required skills or description
        if match_count > 0:  # Only include if there's at least one match
            processed_jobs[job.id] = {
                'job': job,
                'match_score': round(match_score, 1),
                'match_count': match_count,
                'total_required': total_required,
                'has_applied': Application.objects.filter(
                    job=job,
                    applicant=request.user
                ).exists(),
                'job_skills_display': [
                    skill.strip() for skill in (job.required_skills or '').replace(',', '\n').split('\n')
                    if skill.strip()
                ][:5]  # Limit to 5 skills for display
            }
    
    # Convert processed jobs to list and sort by match score (descending) and publish date
    recommended_jobs = sorted(
        processed_jobs.values(),
        key=lambda x: (-x['match_score'], x['job'].published_at or x['job'].created_at)
    )[:20]  # Limit to top 20 recommendations
    
    context = {
        'template_data': {
            'recommended_jobs': recommended_jobs,
            'user_skills': user_skills_list,
            'title': 'Job Recommendations'
        }
    }
    return render(request, 'jobs/recommendations.html', context)

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
    If user has set preferred location and commute radius, automatically filter jobs.
    """
    # Get user's commute preferences if they exist
    user_lat = None
    user_lng = None
    user_radius = None
    user_location_address = None
    
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        profile = request.user.profile
        if profile.preferred_location_lat and profile.preferred_location_lng:
            user_lat = float(profile.preferred_location_lat)
            user_lng = float(profile.preferred_location_lng)
            user_radius = profile.commute_radius
            user_location_address = profile.preferred_location_address
    
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
        # Calculate distance if user has preferred location
        distance_from_user = None
        within_radius = True  # Default to showing all offices
        
        if user_lat and user_lng and user_radius:
            distance_from_user = haversine(user_lat, user_lng, float(office.latitude), float(office.longitude))
            within_radius = distance_from_user <= user_radius
        
        # Only include offices within user's commute radius (if set)
        if not within_radius:
            continue
        
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
        
        office_info = {
            'id': office.id,
            'company_name': office.company.name,
            'address': office.address,
            'city': office.city,
            'state': office.state,
            'country': office.country,
            'latitude': float(office.latitude),
            'longitude': float(office.longitude),
            'job_count': len(jobs_at_office),
            'distance_from_user': round(distance_from_user, 1) if distance_from_user else None,
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
        }
        office_data.append(office_info)
    
    context = {
        'template_data': {
            'title': 'Jobs Map',
            'office_data': json.dumps(office_data),
            'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
            'user_location': {
                'lat': user_lat,
                'lng': user_lng,
                'radius': user_radius,
                'address': user_location_address
            } if user_lat and user_lng else None
        }
    }
    
    return render(request, 'jobs/job_map.html', context)


@csrf_exempt
def filter_by_distance(request):
    """Return jobs within a given distance of the user's current location."""
    try:
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
        max_distance = float(request.GET.get('distance', 10))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid coordinates'}, status=400)

    # Get all office locations with published jobs
    office_locations = OfficeLocation.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
        job__status=Job.Status.PUBLISHED
    ).select_related('company').distinct()
    
    filtered_offices = []
    for office in office_locations:
        dist = haversine(lat, lng, float(office.latitude), float(office.longitude))
        if dist <= max_distance:
            jobs_at_office = Job.objects.filter(
                office_location=office,
                status=Job.Status.PUBLISHED
            )
            
            filtered_offices.append({
                'id': office.id,
                'company_name': office.company.name,
                'address': office.address,
                'city': office.city,
                'state': office.state,
                'country': office.country,
                'latitude': float(office.latitude),
                'longitude': float(office.longitude),
                'distance': round(dist, 2),
                'job_count': jobs_at_office.count()
            })

    return JsonResponse({'offices': filtered_offices})


class CandidateSearchView(LoginRequiredMixin, RecruiterRequiredMixin, ListView):
    """View for recruiters to search for candidates by skills, location, and experience"""
    model = Profile
    template_name = 'jobs/candidate_search.html'
    context_object_name = 'candidates'
    paginate_by = 10
    
    def get_queryset(self):
        # Start with public profiles only
        queryset = Profile.objects.filter(
            is_public=True
        ).select_related('user').order_by('-updated_at')
        
        # Get form data
        form = CandidateSearchForm(self.request.GET)
        
        if form.is_valid():
            cleaned_data = form.cleaned_data
            
            # Skills search
            if cleaned_data.get('skills'):
                skills_query = cleaned_data['skills']
                # Parse search skills
                search_skills = [skill.strip().lower() for skill in skills_query.split(',') if skill.strip()]
                
                if search_skills:
                    # Filter profiles that have at least one matching skill
                    skills_filter = Q()
                    for skill in search_skills:
                        skills_filter |= Q(skills__icontains=skill)
                    queryset = queryset.filter(skills_filter)
            
            # Experience search
            if cleaned_data.get('experience'):
                experience_query = cleaned_data['experience']
                queryset = queryset.filter(
                    Q(experience__icontains=experience_query) |
                    Q(education__icontains=experience_query)
                )
            
            # Location search
            search_lat = cleaned_data.get('search_lat')
            search_lng = cleaned_data.get('search_lng')
            distance_radius = cleaned_data.get('distance_radius')
            
            if search_lat and search_lng and distance_radius:
                try:
                    user_lat = float(search_lat)
                    user_lng = float(search_lng)
                    radius = float(distance_radius)
                    
                    # Filter candidates within radius
                    filtered_candidates = []
                    for profile in queryset:
                        # Include candidates without location preferences
                        if not profile.preferred_location_lat or not profile.preferred_location_lng:
                            filtered_candidates.append(profile.id)
                            continue
                            
                        # Check distance for candidates with location preferences
                        distance = haversine(
                            user_lat, user_lng,
                            float(profile.preferred_location_lat),
                            float(profile.preferred_location_lng)
                        )
                        if distance <= radius:
                            filtered_candidates.append(profile.id)
                    
                    queryset = queryset.filter(id__in=filtered_candidates)
                except (ValueError, TypeError):
                    pass  # Invalid coordinates, skip filter
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = CandidateSearchForm(self.request.GET)
        context['form'] = form
        
        # Process candidates for display with matching information
        candidates_with_matches = []
        search_skills = []
        
        # Get search skills if provided
        if form.is_valid() and form.cleaned_data.get('skills'):
            search_skills = [skill.strip().lower() for skill in form.cleaned_data['skills'].split(',') if skill.strip()]
        
        # Get search location for distance calculation
        search_lat = None
        search_lng = None
        if form.is_valid():
            search_lat = form.cleaned_data.get('search_lat')
            search_lng = form.cleaned_data.get('search_lng')
        
        for candidate in context['candidates']:
            # Process skills for display
            skills_list = []
            if candidate.skills:
                # Split by both commas and newlines, then clean up
                raw_skills = candidate.skills.replace('\n', ',').split(',')
                skills_list = [skill.strip() for skill in raw_skills if skill.strip()]
            
            candidate_data = {
                'profile': candidate,
                'skills_list': skills_list,
                'skills_match_percentage': 0,
                'matching_skills': [],
                'distance_from_search': None
            }
            
            # Calculate skills match
            if search_skills and candidate.skills:
                candidate_skills = [skill.strip().lower() for skill in candidate.skills.replace(',', '\n').split('\n') if skill.strip()]
                matching_skills = [skill for skill in search_skills if skill in candidate_skills]
                
                if matching_skills:
                    candidate_data['matching_skills'] = matching_skills
                    candidate_data['skills_match_percentage'] = round((len(matching_skills) / len(search_skills)) * 100, 1)
            
            # Calculate distance if location search was performed
            if search_lat and search_lng and candidate.preferred_location_lat and candidate.preferred_location_lng:
                try:
                    distance = haversine(
                        float(search_lat), float(search_lng),
                        float(candidate.preferred_location_lat),
                        float(candidate.preferred_location_lng)
                    )
                    candidate_data['distance_from_search'] = round(distance, 1)
                except (ValueError, TypeError):
                    pass
            
            candidates_with_matches.append(candidate_data)
        
        # Sort candidates based on form selection
        sort_by = form.cleaned_data.get('sort_by', 'skills_match') if form.is_valid() else 'skills_match'
        
        if sort_by == 'skills_match':
            candidates_with_matches.sort(key=lambda x: (-x['skills_match_percentage'], x['profile'].updated_at), reverse=True)
        elif sort_by == 'distance':
            candidates_with_matches.sort(key=lambda x: (x['distance_from_search'] or float('inf'), -x['skills_match_percentage']))
        elif sort_by == 'recent':
            candidates_with_matches.sort(key=lambda x: x['profile'].updated_at, reverse=True)
        elif sort_by == 'name':
            candidates_with_matches.sort(key=lambda x: x['profile'].name.lower())
        
        context['candidates'] = candidates_with_matches
        context['GOOGLE_MAPS_API_KEY'] = settings.GOOGLE_MAPS_API_KEY
        
        return context


@login_required
@user_passes_test(lambda u: is_admin(u) or is_recruiter(u))
def kanban_board(request, job_id):
    """Kanban board view for managing applicants"""
    job = get_object_or_404(Job, pk=job_id)
    
    # Verify the recruiter owns this job
    if job.posted_by != request.user and not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to view this job's applications.")
    
    # Get all applications for this job, grouped by status
    applications = Application.objects.filter(job=job).select_related('applicant', 'job__company')
    
    # Group applications by status
    applications_by_status = {}
    for status in Application.Status.choices:
        status_key = status[0]
        applications_by_status[status_key] = [
            app for app in applications if app.status == status_key
        ]
    
    context = {
        'job': job,
        'applications_by_status': applications_by_status,
        'status_choices': Application.Status.choices
    }
    return render(request, 'jobs/kanban_board.html', context)


@login_required
@user_passes_test(lambda u: is_admin(u) or is_recruiter(u))
def update_application_status(request, application_id):
    """Update application status via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    application = get_object_or_404(Application, pk=application_id)
    
    # Verify the recruiter owns the job
    if application.job.posted_by != request.user and not is_admin(request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    new_status = request.POST.get('status')
    if new_status not in dict(Application.Status.choices):
        return JsonResponse({'error': 'Invalid status'}, status=400)
    
    application.status = new_status
    application.save()
    
    return JsonResponse({
        'success': True,
        'status': application.get_status_display(),
        'status_key': application.status
    })


@login_required
@user_passes_test(lambda u: is_admin(u) or is_recruiter(u))
def send_message(request, application_id):
    """Send a message to a candidate"""
    application = get_object_or_404(Application, pk=application_id)
    
    # Verify the recruiter owns the job
    if application.job.posted_by != request.user and not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to send messages for this application.")
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.application = application
            message.sender = request.user
            message.receiver = application.applicant
            message.save()
            messages.success(request, 'Message sent successfully!')
            return redirect('jobs:kanban_board', job_id=application.job.id)
    else:
        # Pre-fill subject with job title
        initial_subject = f"Re: Application for {application.job.title}"
        form = MessageForm(initial={'subject': initial_subject})
    
    context = {
        'application': application,
        'form': form
    }
    return render(request, 'jobs/send_message.html', context)


@login_required
@user_passes_test(lambda u: is_admin(u) or is_recruiter(u))
def send_email(request, application_id):
    """Send an email to a candidate through the platform"""
    application = get_object_or_404(Application, pk=application_id)
    
    # Verify the recruiter owns the job
    if application.job.posted_by != request.user and not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to send emails for this application.")
    
    # Check if applicant has an email address
    if not application.applicant.email:
        messages.error(request, 'This candidate has not provided an email address. Please use in-platform messaging instead.')
        return redirect('jobs:kanban_board', job_id=application.job.id)
    
    if request.method == 'POST':
        form = ApplicationEmailForm(request.POST)
        if form.is_valid():
            # Save email record
            email_record = form.save(commit=False)
            email_record.application = application
            email_record.sent_by = request.user
            email_record.save()
            
            # Send the actual email
            from django.core.mail import send_mail
            from django.conf import settings
            
            try:
                send_mail(
                    subject=form.cleaned_data['subject'],
                    message=form.cleaned_data['message'],
                    from_email=settings.DEFAULT_FROM_EMAIL or request.user.email,
                    recipient_list=[application.applicant.email],
                    fail_silently=False,
                )
                messages.success(request, f'Email sent to {application.applicant.email} successfully!')
            except Exception as e:
                messages.error(request, f'Failed to send email: {str(e)}')
            
            return redirect('jobs:kanban_board', job_id=application.job.id)
    else:
        # Pre-fill subject with job title
        initial_subject = f"Re: Application for {application.job.title}"
        form = ApplicationEmailForm(initial={'subject': initial_subject})
    
    context = {
        'application': application,
        'form': form,
        'recipient_email': application.applicant.email
    }
    return render(request, 'jobs/send_email.html', context)


@login_required
def view_messages(request, application_id):
    """View conversation for an application"""
    application = get_object_or_404(Application, pk=application_id)
    
    # Verify user has permission to view messages
    if request.user != application.applicant and (application.job.posted_by != request.user and not is_admin(request.user)):
        return HttpResponseForbidden("You don't have permission to view these messages.")
    
    # Get all messages for this application
    conversation_messages = Message.objects.filter(application=application).select_related('sender', 'receiver')
    
    # Mark messages as read for the current user
    Message.objects.filter(
        application=application,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)
    
    context = {
        'application': application,
        'messages': conversation_messages
    }
    return render(request, 'jobs/view_messages.html', context)


@login_required
def reply_message(request, application_id):
    """Reply to a message conversation"""
    application = get_object_or_404(Application, pk=application_id)
    
    # Verify user has permission
    if request.user != application.applicant and (application.job.posted_by != request.user and not is_admin(request.user)):
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.application = application
            message.sender = request.user
            # Set receiver to the other party
            if request.user == application.applicant:
                message.receiver = application.job.posted_by
            else:
                message.receiver = application.applicant
            message.save()
            messages.success(request, 'Message sent!')
            return redirect('jobs:view_messages', application_id=application_id)
    else:
        form = MessageForm()
    
    context = {
        'application': application,
        'form': form
    }
    return render(request, 'jobs/reply_message.html', context)


@login_required
def view_emails(request, application_id):
    """View emails sent to a job seeker for a specific application"""
    application = get_object_or_404(Application, pk=application_id)
    
    # Verify this is the applicant
    if application.applicant != request.user:
        return HttpResponseForbidden("You don't have permission to view these emails.")
    
    # Get all emails sent for this application
    emails = ApplicationEmail.objects.filter(
        application=application
    ).select_related('sent_by').order_by('-sent_at')
    
    context = {
        'application': application,
        'emails': emails
    }
    return render(request, 'jobs/view_emails.html', context)
