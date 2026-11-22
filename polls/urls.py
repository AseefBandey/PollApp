from django.urls import path
from . import views
from . import api

app_name = 'polls'

urlpatterns = [
    # UI Views
    path('', views.polls_list, name='list'),
    path('add/', views.polls_add, name='add'),
    path('edit/<int:poll_id>/', views.polls_edit, name='edit'),
    path('delete/<int:poll_id>/', views.polls_delete, name='delete'),
    path('end/<int:poll_id>/', views.end_poll, name='end_poll'),
    path('<int:poll_id>/', views.poll_detail, name='detail'),
    path('<int:poll_id>/vote/', views.poll_vote, name='vote'),
    path('<int:poll_id>/results/', views.poll_result, name='results'),
    path('<int:poll_id>/results/data/', views.poll_result_api, name='results_data'),

    # REST API Endpoints
    path('api/polls/', api.PollListCreateAPI.as_view(), name='api_poll_list_create'),
    path('api/polls/<int:pk>/', api.PollDetailAPI.as_view(), name='api_poll_detail'),
    path('api/polls/<int:pk>/vote/', api.PollVoteAPI.as_view(), name='api_poll_vote'),
    path('api/polls/<int:pk>/results/', api.PollResultAPI.as_view(), name='api_poll_results'),
]
