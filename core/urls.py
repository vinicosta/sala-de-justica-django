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

    # ── Editar edição ──────────────────────────────────────────────────────
    path("quadrinhos/<int:issue_id>/editar/", views.issue_edit,
         {"type_id": 1, "type_label": "Quadrinhos"}, name="quadrinhos_edit"),
    path("livros/<int:issue_id>/editar/",     views.issue_edit,
         {"type_id": 2, "type_label": "Livros"},     name="livros_edit"),
    path("revistas/<int:issue_id>/editar/",   views.issue_edit,
         {"type_id": 3, "type_label": "Revistas"},   name="revistas_edit"),

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

    # ── Cadastro de Autores ─────────────────────────────────────────────────
    path("autores/",               views.author_list,   name="autores"),
    path("autores/novo/",          views.author_create, name="autor_create"),
    path("autores/<int:author_id>/editar/",   views.author_edit,   name="autor_edit"),
    path("autores/<int:author_id>/excluir/",  views.author_delete, name="autor_delete"),

    # ── Cadastro de Editoras ─────────────────────────────────────────────────
    path("editoras/",               views.publisher_list,   name="editoras"),
    path("editoras/novo/",          views.publisher_create, name="editora_create"),
    path("editoras/<int:publisher_id>/editar/",  views.publisher_edit,   name="editora_edit"),
    path("editoras/<int:publisher_id>/excluir/", views.publisher_delete, name="editora_delete"),

    # ── Cadastro de Formatos ─────────────────────────────────────────────────
    path("formatos/",               views.format_list,   name="formatos"),
    path("formatos/novo/",          views.format_create, name="formato_create"),
    path("formatos/<int:format_id>/editar/",  views.format_edit,   name="formato_edit"),
    path("formatos/<int:format_id>/excluir/", views.format_delete, name="formato_delete"),

    # ── Cadastro de Gêneros ──────────────────────────────────────────────────
    path("generos/",               views.genre_list,   name="generos"),
    path("generos/novo/",          views.genre_create, name="genero_create"),
    path("generos/<int:genre_id>/editar/",  views.genre_edit,   name="genero_edit"),
    path("generos/<int:genre_id>/excluir/", views.genre_delete, name="genero_delete"),

    # ── Cadastro de Subgêneros ───────────────────────────────────────────────
    path("subgeneros/",               views.subgenre_list,   name="subgeneros"),
    path("subgeneros/novo/",          views.subgenre_create, name="subgenero_create"),
    path("subgeneros/<int:subgenre_id>/editar/",  views.subgenre_edit,   name="subgenero_edit"),
    path("subgeneros/<int:subgenre_id>/excluir/", views.subgenre_delete, name="subgenero_delete"),

    # ── Cadastro de Periodicidades ───────────────────────────────────────────
    path("periodicidades/",               views.periodicity_list,   name="periodicidades"),
    path("periodicidades/novo/",          views.periodicity_create, name="periodicidade_create"),
    path("periodicidades/<int:periodicity_id>/editar/",  views.periodicity_edit,   name="periodicidade_edit"),
    path("periodicidades/<int:periodicity_id>/excluir/", views.periodicity_delete, name="periodicidade_delete"),

    # ── Editar título ────────────────────────────────────────────────────────
    path("quadrinhos/titulo/<int:title_id>/editar/", views.title_edit,
         {"type_id": 1, "type_label": "Quadrinhos", "slug": "quadrinhos"}, name="quadrinhos_titulo_edit"),
    path("livros/titulo/<int:title_id>/editar/",     views.title_edit,
         {"type_id": 2, "type_label": "Livros",     "slug": "livros"},     name="livros_titulo_edit"),
    path("revistas/titulo/<int:title_id>/editar/",   views.title_edit,
         {"type_id": 3, "type_label": "Revistas",   "slug": "revistas"},   name="revistas_titulo_edit"),
]