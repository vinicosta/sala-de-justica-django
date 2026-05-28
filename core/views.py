# core/views.py

import json
import random
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import CollectionItem, Issue, ReadItem, ReadingList, Title


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_search(q: str):
    if not q:
        return Q()
    if "#" in q:
        parts = q.split("#", 1)
        title_part  = parts[0].strip()
        number_part = parts[1].strip()
        filters = Q()
        if title_part:
            filters &= Q(title__name__icontains=title_part)
        if number_part:
            filters &= Q(issue_number__icontains=number_part)
        return filters
    return (
        Q(title__name__icontains=q)
        | Q(name__icontains=q)
        | Q(subtitle__icontains=q)
    )


def _next_issues_for_user(user, type_id: int) -> list:
    """
    Para cada título na lista de leitura do usuário (filtrado por type_id),
    retorna o ID da próxima edição a ser lida.
    """
    title_ids = list(
        ReadingList.objects
        .filter(user=user, title__type_id=type_id)
        .values_list("title_id", flat=True)
    )

    if not title_ids:
        return []

    read_issue_ids = set(
        ReadItem.objects
        .filter(user=user)
        .values_list("issue_id", flat=True)
    )

    next_ids = []

    for title_id in title_ids:
        issues = list(
            Issue.objects
            .filter(title_id=title_id)
            .order_by("date_publication", "issue_number")
            .values_list("id", flat=True)
        )

        if not issues:
            continue

        last_read_index = -1
        for i, issue_id in enumerate(issues):
            if issue_id in read_issue_ids:
                last_read_index = i

        next_index = last_read_index + 1

        if next_index >= len(issues):
            continue

        next_ids.append(issues[next_index])

    return next_ids


def _type_slug(type_id: int) -> str:
    return {1: "quadrinhos", 2: "livros", 3: "revistas"}.get(type_id, "quadrinhos")


def _ordered_issues_for_title(title_id: int):
    """Retorna todas as edições de um título em ordem cronológica."""
    return list(
        Issue.objects
        .filter(title_id=title_id)
        .order_by("date_publication", "issue_number")
        .values_list("id", flat=True)
    )


# ── Views públicas ────────────────────────────────────────────────────────────

@login_required
def issue_list(request, type_id: int, type_label: str):
    user = request.user
    q    = request.GET.get("q", "").strip()

    next_issue_ids = _next_issues_for_user(user, type_id)

    if not next_issue_ids:
        context = {
            "type_label":    type_label,
            "type_id":       type_id,
            "issues":        [],
            "total":         0,
            "collected_ids": set(),
            "read_ids":      set(),
            "q":             q,
        }
        return render(request, "core/issue_list.html", context)

    qs = (
        Issue.objects
        .filter(pk__in=next_issue_ids)
        .select_related("title", "title__publisher", "title__type")
        .order_by("date_publication", "title__name", "issue_number")
    )

    if q:
        qs = qs.filter(_parse_search(q))

    collected_ids = set(
        CollectionItem.objects.filter(user=user).values_list("issue_id", flat=True)
    )
    read_ids = set(
        ReadItem.objects.filter(user=user).values_list("issue_id", flat=True)
    )

    context = {
        "type_label":    type_label,
        "type_id":       type_id,
        "issues":        qs,
        "total":         qs.count(),
        "collected_ids": collected_ids,
        "read_ids":      read_ids,
        "q":             q,
    }
    return render(request, "core/issue_list.html", context)


@login_required
def issue_detail(request, type_id: int, type_label: str, issue_id: int):
    user  = request.user
    issue = get_object_or_404(
        Issue.objects.select_related(
            "title", "title__publisher", "title__type",
            "title__genre", "title__subgenre", "title__format",
        ).prefetch_related("authors"),
        pk=issue_id,
        title__type_id=type_id,
    )

    # Navegação — todas as edições do título em ordem
    sibling_ids = _ordered_issues_for_title(issue.title_id)
    try:
        current_index = sibling_ids.index(issue_id)
    except ValueError:
        current_index = 0

    total_siblings = len(sibling_ids)
    first_id   = sibling_ids[0]                          if total_siblings > 0 else None
    prev_id    = sibling_ids[current_index - 1]          if current_index > 0 else None
    next_id    = sibling_ids[current_index + 1]          if current_index < total_siblings - 1 else None
    last_id    = sibling_ids[-1]                         if total_siblings > 0 else None

    slug = _type_slug(type_id)

    nav = {
        "first_url": f"/{slug}/{first_id}/" if first_id and first_id != issue_id else None,
        "prev_url":  f"/{slug}/{prev_id}/"  if prev_id else None,
        "next_url":  f"/{slug}/{next_id}/"  if next_id else None,
        "last_url":  f"/{slug}/{last_id}/"  if last_id and last_id != issue_id else None,
        "grid_url":  f"/{slug}/titulo/{issue.title_id}/",
        "position":  f"{current_index + 1} / {total_siblings}",
    }

    # Estado do usuário para esta edição
    collection_item = CollectionItem.objects.filter(issue=issue, user=user).first()
    is_read = ReadItem.objects.filter(issue=issue, user=user).exists()

    context = {
        "issue":           issue,
        "title":           issue.title,
        "type_label":      type_label,
        "type_id":         type_id,
        "slug":            slug,
        "nav":             nav,
        "collection_item": collection_item,
        "in_collection":   collection_item is not None,
        "is_read":         is_read,
        # Mostrar formato só para quadrinhos (type_id=1)
        "show_format":     type_id == 1,
        # Mostrar ISBN e autores só para livros (type_id=2)
        "show_isbn":       type_id == 2,
        "show_authors":    type_id == 2,
        # Mostrar gênero só para livros
        "show_genre":      type_id == 2,
    }
    return render(request, "core/issue_detail.html", context)


# ── Ações AJAX ────────────────────────────────────────────────────────────────

@login_required
@require_POST
def toggle_collection(request, issue_id: int):
    issue = get_object_or_404(Issue, pk=issue_id)
    user  = request.user

    item, created = CollectionItem.objects.get_or_create(
        issue=issue, user=user,
        defaults={"has_physical": True, "has_digital": False},
    )

    if not created:
        body = json.loads(request.body or "{}")
        if body.get("confirm"):
            item.delete()
            return JsonResponse({"status": "removed"})
        return JsonResponse({"status": "confirm_needed"})

    return JsonResponse({"status": "added"})


@login_required
@require_POST
def toggle_read(request, issue_id: int):
    issue = get_object_or_404(Issue, pk=issue_id)
    user  = request.user

    item, created = ReadItem.objects.get_or_create(
        issue=issue, user=user,
        defaults={"is_reread": False},
    )

    if not created:
        body = json.loads(request.body or "{}")
        if body.get("confirm"):
            item.delete()
            return JsonResponse({"status": "removed"})
        return JsonResponse({"status": "confirm_needed"})

    return JsonResponse({"status": "added"})