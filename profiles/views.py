from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile
from .forms import CustomProfileCreationForm


@login_required
def create(request):
    """Create a new profile for the user"""
    # Check if user already has a profile
    if hasattr(request.user, 'profile'):
        messages.info(request, 'You already have a profile. Redirecting to edit.')
        return redirect('profiles:profiles.edit')
    
    if request.method == 'POST':
        form = CustomProfileCreationForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Profile created successfully!')
            return redirect('profiles:profiles.detail')
    else:
        form = CustomProfileCreationForm()
    
    context = {
        'template_data': {
            'form': form,
            'title': 'Create Profile'
        }
    }
    return render(request, 'profiles/create.html', context)


@login_required
def detail(request):
    """View the user's profile"""
    profile = get_object_or_404(Profile, user=request.user)
    
    context = {
        'template_data': {
            'profile': profile,
            'title': 'My Profile'
        }
    }
    return render(request, 'profiles/detail.html', context)


@login_required
def edit(request):
    """Edit the user's profile"""
    profile = get_object_or_404(Profile, user=request.user)
    
    if request.method == 'POST':
        form = CustomProfileCreationForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profiles:profiles.detail')
    else:
        form = CustomProfileCreationForm(instance=profile)
    
    context = {
        'template_data': {
            'form': form,
            'profile': profile,
            'title': 'Edit Profile'
        }
    }
    return render(request, 'profiles/edit.html', context)