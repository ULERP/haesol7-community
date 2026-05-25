from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('community/', include('community.urls')),
    path('', include('hello_world.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
