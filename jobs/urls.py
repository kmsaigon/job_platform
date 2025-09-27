from django.urls import path
from . import views

app_name = 'jobs'
urlpatterns = [
    path('', views.JobSearchView.as_view(), name='public_list'),
    path('search/', views.JobSearchView.as_view(), name='job_search'),
    path('<int:pk>-<slug:slug>/', views.JobPublicDetailView.as_view(), name='public_detail'),
    path('recruiter/', views.JobMyListView.as_view(), name='my_list'),
    path('recruiter/new', views.JobCreateView.as_view(), name='create'),
    path('recruiter/<int:pk>/edit', views.JobUpdateView.as_view(), name='edit'),
    path('recruiter/<int:pk>/publish', views.job_publish, name='publish'),
    path('recruiter/<int:pk>/unpublish', views.job_unpublish, name='unpublish'),
    path('recruiter/<int:pk>/close', views.job_close, name='close'),
]


