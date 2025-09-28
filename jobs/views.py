from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import JobForm
from .models import Job, JobStatusHistory


def is_admin(user):
    return user.is_superuser or user.groups.filter(name='admin').exists()


def is_recruiter(user):
    return user.groups.filter(name='recruiter').exists()


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
        messages.info(request, 'Job closed.')
    return redirect('jobs:my_list')


