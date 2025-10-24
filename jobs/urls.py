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
    path('<int:pk>/apply/', views.apply_to_job, name='apply'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('application/<int:application_id>/withdraw/', views.withdraw_application, name='withdraw_application'),
    path('map/', views.job_map, name='job_map'),
    path('api/filter_by_distance/', views.filter_by_distance, name='filter_by_distance'),
]


