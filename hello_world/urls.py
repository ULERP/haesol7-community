from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', include('hello_world.core.urls')),
    path('admin/', admin.site.urls),
    path('community/', include('community.urls')),
    path('__reload__/', include('django_browser_reload.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# media 파일은 항상 서빙 (PythonAnywhere 포함)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'hello_world.core.views.error_404'
handler500 = 'hello_world.core.views.error_500'
