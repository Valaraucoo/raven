from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.documentation import include_docs_urls
from rest_framework.schemas import get_schema_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('', include('users.urls', namespace='users')),
    path('', include('courses.urls', namespace='courses')),
    path('support/', include('support.urls', namespace='support')),

    path('schema/', get_schema_view(title='API Docs', description='Raven app API'), name='api-schema'),
    path('docs/', include_docs_urls(title='API Docs'), name='docs'),
]

if bool(settings.DEBUG):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
