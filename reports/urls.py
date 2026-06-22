from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='list'),
    path('create/', views.report_create, name='create'),
    path('<int:pk>/', views.report_detail, name='detail'),
    path('<int:pk>/inline-update/', views.report_inline_update, name='inline_update'),
    path('<int:pk>/status/', views.report_update_status, name='update_status'),
]