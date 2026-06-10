# core/admin.py

import re

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db.models import Q
from unfold.admin import ModelAdmin, TabularInline

from .models import (
    Author,
    CollectionItem,
    Format,
    Genre,
    Issue,
    Periodicity,
    Publisher,
    ReadingList,
    ReadItem,
    Subgenre,
    Title,
    Type,
)

from .gap_detection import fill_gaps


# ── Inlines ──────────────────────────────────────────────────────────────────

class FormatInline(TabularInline):
    model = Format
    extra = 1


class SubgenreInline(TabularInline):
    model = Subgenre
    extra = 1


class IssueInline(TabularInline):
    model = Issue
    extra = 0
    show_change_link = True
    fields = ("issue_number", "name", "date_publication", "is_estimated", "number_pages")
    readonly_fields = ("is_estimated",)


# ── Busca inteligente para Issue ──────────────────────────────────────────────
#
# Suporta dois formatos:
#   "batman"       → busca em title__name e issue.name/subtitle
#   "batman #34"   → busca title__name contendo "batman"
#                    E issue_number contendo "34"
#
class IssueSearchMixin:
    """
    Mixin que sobrescreve get_search_results para suportar a sintaxe
    "título #número", cobrindo o catálogo completo (sem pré-filtro de coleção).
    """

    def get_search_results(self, request, queryset, search_term):
        if not search_term:
            return queryset, False

        use_distinct = False

        if "#" in search_term:
            parts = search_term.split("#", 1)
            title_part = parts[0].strip()
            number_part = parts[1].strip()

            filters = Q(title__type__id__in=[1, 2, 3])  # garante catálogo completo
            if title_part:
                filters &= Q(title__name__icontains=title_part)
            if number_part:
                filters &= Q(issue_number__icontains=number_part)

            queryset = queryset.filter(filters)
            use_distinct = True
        else:
            queryset = queryset.filter(
                Q(title__name__icontains=search_term)
                | Q(name__icontains=search_term)
                | Q(subtitle__icontains=search_term)
                | Q(isbn__icontains=search_term)
            )
            use_distinct = True

        return queryset, use_distinct


# ── Auxiliares ───────────────────────────────────────────────────────────────

@admin.register(Type)
class TypeAdmin(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    inlines = [FormatInline]


@admin.register(Format)
class FormatAdmin(ModelAdmin):
    list_display = ("name", "type")
    search_fields = ("name",)
    list_filter = ("type",)


@admin.register(Publisher)
class PublisherAdmin(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Periodicity)
class PeriodicityAdmin(ModelAdmin):
    list_display = ("name", "date_interval_number", "date_interval")
    search_fields = ("name",)


@admin.register(Genre)
class GenreAdmin(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    inlines = [SubgenreInline]


@admin.register(Subgenre)
class SubgenreAdmin(ModelAdmin):
    list_display = ("name", "genre")
    search_fields = ("name",)
    list_filter = ("genre",)


@admin.register(Author)
class AuthorAdmin(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


# ── Core ─────────────────────────────────────────────────────────────────────

@admin.register(Title)
class TitleAdmin(ModelAdmin):
    list_display = ("name", "type", "publisher", "status", "origin", "genre")
    search_fields = ("name",)
    list_filter = ("type", "status", "origin", "genre", "publisher")
    inlines = [IssueInline]


@admin.register(Issue)
class IssueAdmin(IssueSearchMixin, ModelAdmin):
    # search_fields precisa ter ao menos um campo para a barra de busca aparecer;
    # a lógica real está no mixin acima.
    search_fields = ("name",)

    list_display = (
        "title",
        "issue_number",
        "name",
        "date_publication",
        "number_pages",
        "is_estimated",
    )
    list_filter = ("title__type", "is_estimated", "title__publisher")
    filter_horizontal = ("authors",)

    # Garante que o filtro por tipo (vindo do link do menu) funcione corretamente.
    # O parâmetro title__type__id__exact é reconhecido pelo list_filter acima.

    # Sobrescreve save_model para rodar gap detection após salvar uma edição.
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Só roda gap detection se issue_number for numérico
        if obj.issue_number and re.match(r'^\d+', obj.issue_number.strip()):
            fill_gaps(obj.title)


# ── Usuário ───────────────────────────────────────────────────────────────────

@admin.register(CollectionItem)
class CollectionItemAdmin(ModelAdmin):
    list_display = ("issue", "user", "added_date", "has_physical", "has_digital")
    search_fields = ("issue__name", "issue__title__name")
    list_filter = ("has_physical", "has_digital", "user", "issue__title__type")


@admin.register(ReadItem)
class ReadItemAdmin(ModelAdmin):
    list_display = ("issue", "user", "read_date", "is_reread")
    search_fields = ("issue__name", "issue__title__name")
    list_filter = ("is_reread", "user")


@admin.register(ReadingList)
class ReadingListAdmin(ModelAdmin):
    list_display = ("title", "user", "created_at")
    search_fields = ("title__name",)
    list_filter = ("user",)