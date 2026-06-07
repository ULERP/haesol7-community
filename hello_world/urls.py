from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('favicon.ico'), permanent=True)),
    path('', include('hello_world.core.urls')),
    path('admin/', admin.site.urls),
    path('community/', include('community.urls')),
    path('__reload__/', include('django_browser_reload.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'hello_world.core.views.error_404'
handler500 = 'hello_world.core.views.error_500'
