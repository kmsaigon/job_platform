from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('create', views.create, name='profiles.create'),
    path('view', views.detail, name='profiles.detail'),
    path('edit', views.edit, name='profiles.edit'),
]