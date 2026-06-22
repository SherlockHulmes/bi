from django.urls import path
from . import views

app_name = 'scheduler'

urlpatterns = [
    path('', views.task_list, name='list'),
    path('create/', views.task_create, name='create'),
    path('<int:pk>/edit/', views.task_edit, name='edit'),
    path('<int:pk>/toggle/', views.task_toggle, name='toggle'),
    path('<int:pk>/execute/', views.task_execute, name='execute'),
    path('<int:pk>/copy/', views.task_copy, name='copy'),
    path('<int:pk>/notify/', views.task_notify, name='notify'),
    path('<int:pk>/send-file/', views.task_send_file, name='send_file'),
    path('<int:pk>/delete/', views.task_delete, name='delete'),
    path('logs/', views.execution_logs, name='logs'),
    path('logs/<int:pk>/detail/', views.log_detail, name='log_detail'),
]