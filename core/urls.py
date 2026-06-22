from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('import/', views.import_data, name='import_data'),
    path('api/preview/', views.preview, name='preview'),
    path('api/import/', views.do_import, name='do_import'),
    path('api/dashboard/card/<int:card_id>/', views.dashboard_card_data, name='dashboard_card_data'),
    path('tools/loan-schedule/', views.loan_schedule, name='loan_schedule'),
    path('accounts/password/', views.change_password, name='change_password'),
]
