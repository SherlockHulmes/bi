from django.urls import path
from . import views

app_name = 'data_quality'

urlpatterns = [
    path('', views.rule_list, name='rule_list'),
    path('create/', views.rule_create, name='rule_create'),
    path('<int:pk>/edit/', views.rule_edit, name='rule_edit'),
    path('<int:pk>/execute/', views.rule_execute, name='rule_execute'),
    path('<int:pk>/logs/', views.rule_logs, name='rule_logs'),
    path('<int:pk>/copy/', views.rule_copy, name='rule_copy'),
    path('<int:pk>/delete/', views.rule_delete, name='rule_delete'),
    path('logs/', views.all_logs, name='all_logs'),
]