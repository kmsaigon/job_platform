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
    path('recruiter/candidates/', views.CandidateSearchView.as_view(), name='candidate_search'),
    path('<int:pk>/apply/', views.apply_to_job, name='apply'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('application/<int:application_id>/withdraw/', views.withdraw_application, name='withdraw_application'),
    path('map/', views.job_map, name='job_map'),
    path('api/filter_by_distance/', views.filter_by_distance, name='filter_by_distance'),
    path('recruiter/job/<int:job_id>/recommendations/', views.candidate_recommendations, name='candidate_recommendations'),
    
    # Kanban and messaging features
    path('recruiter/job/<int:job_id>/kanban/', views.kanban_board, name='kanban_board'),
    path('recruiter/application/<int:application_id>/update-status/', views.update_application_status, name='update_application_status'),
    path('recruiter/application/<int:application_id>/send-message/', views.send_message, name='send_message'),
    path('recruiter/application/<int:application_id>/send-email/', views.send_email, name='send_email'),
    path('application/<int:application_id>/messages/', views.view_messages, name='view_messages'),
    path('application/<int:application_id>/reply/', views.reply_message, name='reply_message'),
    path('application/<int:application_id>/emails/', views.view_emails, name='view_emails'),
    
    # Saved candidate searches
    path('recruiter/candidates/save/', views.save_candidate_search, name='save_search'),
    path('recruiter/candidates/saved/', views.saved_searches, name='saved_searches'),
    path('recruiter/candidates/saved/<int:search_id>/run/', views.run_saved_search, name='run_saved_search'),
    path('recruiter/candidates/saved/<int:search_id>/delete/', views.delete_saved_search, name='delete_saved_search'),
    path('recruiter/candidates/saved/<int:search_id>/toggle-notifications/', views.toggle_search_notifications, name='toggle_search_notifications'),
]
