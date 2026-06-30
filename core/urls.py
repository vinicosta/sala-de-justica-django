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

    # ── Sorteio de livro ───────────────────────────────────────────────────
    path("livros/sortear/", views.sortear_livro, name="sortear_livro"),

    # ── Criar edição (form completo ou compacto via ?title_id=X) ──────────
    path("quadrinhos/nova/", views.issue_create,
         {"type_id": 1, "type_label": "Quadrinhos"}, name="quadrinhos_create"),
    path("livros/nova/",     views.issue_create,
         {"type_id": 2, "type_label": "Livros"},     name="livros_create"),
    path("revistas/nova/",   views.issue_create,
         {"type_id": 3, "type_label": "Revistas"},   name="revistas_create"),

    # ── Upload assíncrono de capa ──────────────────────────────────────────
    path("api/upload-cover/", views.upload_cover, name="upload_cover"),

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
    path("formato/toggle/<int:issue_id>/", views.toggle_format,     name="toggle_format"),
    path("lista/toggle/<int:title_id>/",   views.toggle_reading_list, name="toggle_reading_list"),

    # ── Detalhe de título ──────────────────────────────────────────────────
    path("quadrinhos/titulo/<int:title_id>/", views.title_detail,
         {"type_id": 1, "type_label": "Quadrinhos", "slug": "quadrinhos"}, name="quadrinhos_titulo"),
    path("livros/titulo/<int:title_id>/",     views.title_detail,
         {"type_id": 2, "type_label": "Livros",     "slug": "livros"},     name="livros_titulo"),
    path("revistas/titulo/<int:title_id>/",   views.title_detail,
         {"type_id": 3, "type_label": "Revistas",   "slug": "revistas"},   name="revistas_titulo"),
]