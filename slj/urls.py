# slj/urls.py
# Adicione o include abaixo às suas urls existentes

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),          # ← adiciona esta linha
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)