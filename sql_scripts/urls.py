from django.urls import path
from . import views

app_name = 'scripts'

urlpatterns = [
    path('', views.script_list, name='list'),
    path('create/', views.script_create, name='create'),
    path('<int:pk>/', views.script_detail, name='detail'),
    path('<int:pk>/edit/', views.script_edit, name='edit'),
    path('<int:pk>/execute/', views.script_execute, name='execute'),
    path('<int:pk>/download/', views.script_download_result, name='download'),
    path('<int:pk>/delete/', views.script_delete, name='delete'),
]