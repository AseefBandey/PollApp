from django.urls import path
from . import views

app_name = 'polls'

urlpatterns = [
    path('', views.polls_list, name='list'),
    path('add/', views.polls_add, name='add'),
    path('edit/<int:poll_id>/', views.polls_edit, name='edit'),
    path('delete/<int:poll_id>/', views.polls_delete, name='delete'),
    path('<int:poll_id>/', views.poll_detail, name='detail'),
    path('<int:poll_id>/vote/', views.poll_vote, name='vote'),
    path('<int:poll_id>/results/', views.poll_result, name='results'),
]
