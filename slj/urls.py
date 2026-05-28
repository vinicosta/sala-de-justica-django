# slj/urls.py

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from core import views

urlpatterns = [
    path("admin/quadrinhos/", views.issue_list, {"type_id": 1, "type_label": "Quadrinhos"}, name="quadrinhos"),
    path("admin/livros/",     views.issue_list, {"type_id": 2, "type_label": "Livros"},     name="livros"),
    path("admin/revistas/",   views.issue_list, {"type_id": 3, "type_label": "Revistas"},   name="revistas"),
    path("admin/colecao/toggle/<int:issue_id>/", views.toggle_collection, name="toggle_collection"),
    path("admin/lido/toggle/<int:issue_id>/",    views.toggle_read,       name="toggle_read"),
    path("admin/proxima/<int:issue_id>/",        views.next_issue,        name="next_issue"),

    path("admin/", admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)