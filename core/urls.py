# core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("quadrinhos/", views.issue_list, {"type_id": 1, "type_label": "Quadrinhos"}, name="quadrinhos"),
    path("livros/",     views.issue_list, {"type_id": 2, "type_label": "Livros"},     name="livros"),
    path("revistas/",   views.issue_list, {"type_id": 3, "type_label": "Revistas"},   name="revistas"),

    # Ações AJAX
    path("colecao/toggle/<int:issue_id>/", views.toggle_collection, name="toggle_collection"),
    path("lido/toggle/<int:issue_id>/",    views.toggle_read,       name="toggle_read"),
]