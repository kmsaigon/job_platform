from django.shortcuts import render, get_object_or_404
from .forms import CustomProfileCreationForm, CustomErrorList
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

PROFILE_DETAIL_URL = 'profiles:profiles.detail'
PROFILE_CREATE_URL = 'profiles:profiles.create'

@login_required
def create(request):
    if hasattr(request.user, 'profile'):
        messages.info(request, 'You already have a profile. You can edit it from your profile page.')
        return redirect(PROFILE_DETAIL_URL)
    
    template_data = {'title': 'Create Profile'}
    if request.method == 'GET':
        template_data['form'] = CustomProfileCreationForm()
        return render(request, 'profiles/create.html', {'template_data': template_data})
    elif request.method == 'POST':
        form = CustomProfileCreationForm(request.POST, error_class=CustomErrorList)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Profile created successfully!')
            return redirect(PROFILE_DETAIL_URL)
        else:
            template_data['form'] = form
            return render(request, 'profiles/create.html', {'template_data': template_data})


@login_required
def detail(request):
    try:
        profile = request.user.profile
    except AttributeError:
        messages.info(request, 'Please create your profile first.')
        return redirect(PROFILE_CREATE_URL)
    
    template_data = {'title': f"{profile.name}'s Profile", 'profile': profile}
    return render(request, 'profiles/detail.html', {'template_data': template_data})


@login_required
def edit(request):
    try:
        profile = request.user.profile
    except AttributeError:
        messages.info(request, 'Please create your profile first.')
        return redirect(PROFILE_CREATE_URL)
    
    template_data = {'title': 'Edit Profile'}
    if request.method == 'GET':
        template_data['form'] = CustomProfileCreationForm(instance=profile)
        return render(request, 'profiles/edit.html', {'template_data': template_data})
    elif request.method == 'POST':
        form = CustomProfileCreationForm(request.POST, instance=profile, error_class=CustomErrorList)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect(PROFILE_DETAIL_URL)
        else:
            template_data['form'] = form
            return render(request, 'profiles/edit.html', {'template_data': template_data})