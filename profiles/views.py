from django.shortcuts import render
from .forms import CustomProfileCreationForm, CustomErrorList
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def create(request):
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
            return redirect('home.index')
        else:
            template_data['form'] = form
            return render(request, 'profiles/create.html', {'template_data': template_data})


@login_required
def detail(request):
    try:
        profile = request.user.profile
    except Exception:
        return redirect('profiles:profiles.create')
    template_data = {'title': f"{profile.name}'s Profile", 'profile': profile}
    return render(request, 'profiles/detail.html', {'template_data': template_data})