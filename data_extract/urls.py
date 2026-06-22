from django.urls import path
from . import views

app_name = 'data_extract'

urlpatterns = [
    path('', views.query_home, name='home'),
    path('execute/', views.query_execute, name='execute'),
    path('api/tables/', views.api_tables, name='api_tables'),
    path('api/columns/', views.api_columns, name='api_columns'),
    path('templates/', views.template_list, name='template_list'),
    path('templates/<int:pk>/', views.template_detail, name='template_detail'),
    path('templates/<int:pk>/api/', views.template_detail_api, name='template_detail_api'),
    path('save/', views.save_template, name='save_template'),
    path('update/', views.update_template, name='update_template'),
]
