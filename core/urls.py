# core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # ── Listas de leitura ──────────────────────────────────────────────────
    path("quadrinhos/", views.issue_list,
         {"type_id": 1, "type_label": "Quadrinhos"}, name="quadrinhos"),
    path("livros/",     views.issue_list,
         {"type_id": 2, "type_label": "Livros"},     name="livros"),
    path("revistas/",   views.issue_list,
         {"type_id": 3, "type_label": "Revistas"},   name="revistas"),

    # ── Detalhe de edição ──────────────────────────────────────────────────
    path("quadrinhos/<int:issue_id>/", views.issue_detail,
         {"type_id": 1, "type_label": "Quadrinhos"}, name="quadrinhos_detail"),
    path("livros/<int:issue_id>/",     views.issue_detail,
         {"type_id": 2, "type_label": "Livros"},     name="livros_detail"),
    path("revistas/<int:issue_id>/",   views.issue_detail,
         {"type_id": 3, "type_label": "Revistas"},   name="revistas_detail"),

    # ── Ações AJAX ─────────────────────────────────────────────────────────
    path("colecao/toggle/<int:issue_id>/", views.toggle_collection, name="toggle_collection"),
    path("lido/toggle/<int:issue_id>/",    views.toggle_read,       name="toggle_read"),
]