from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('core.urls')),
    path('reports/', include('reports.urls')),
    path('scripts/', include('sql_scripts.urls')),
    path('scheduler/', include('scheduler.urls')),
    path('data-quality/', include('data_quality.urls')),
    path('data-lineage/', include('data_lineage.urls')),
    path('data-extract/', include('data_extract.urls')),
]

if settings.DEBUG:
    from django.views.static import serve
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
