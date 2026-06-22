from django.urls import path
from . import views

app_name = 'data_lineage'

urlpatterns = [
    path('', views.scan_list, name='scan_list'),
    path('scan/', views.scan_execute, name='scan_execute'),
    path('<int:scan_id>/graph/', views.graph_view, name='graph'),
    path('<int:scan_id>/table-detail/', views.table_detail, name='table_detail'),
    path('<int:scan_id>/export/', views.export_excel, name='export'),
    path('<int:scan_id>/update/', views.scan_update, name='update'),
    path('<int:scan_id>/delete/', views.scan_delete, name='delete'),
]