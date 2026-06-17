# core/views.py

import json, random, unicodedata, re
from django.contrib.postgres.search import SearchVector
from django.db.models.functions import Upper
from django.contrib.admin import site as admin_site
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST

from .models import CollectionItem, Issue, ReadItem, ReadingList, Title
from .gap_detection import fill_gaps

# ── Helpers ───────────────────────────────────────────────────────────────────

def _type_slug(type_id: int) -> str:
    return {1: "quadrinhos", 2: "livros", 3: "revistas"}.get(type_id, "quadrinhos")


def _ordered_issues_for_title(title_id: int):
    return list(
        Issue.objects
        .filter(title_id=title_id)
        .order_by("date_publication", "issue_number")
        .values_list("id", flat=True)
    )


def _admin_context(request: object) -> dict:
    ctx = admin_site.each_context(request)
    ctx["is_nav_sidebar_enabled"] = True
    ctx["branding"] = True
    return ctx


def _normalize(text: str) -> str:
    """Remove acentos e caracteres especiais para busca insensível a diacríticos."""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    return ascii_str.lower()


def _next_issues_for_user(user, type_id: int) -> list:
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


def _get_next_issue_data(user, current_issue) -> dict | None:
    read_issue_ids = set(
        ReadItem.objects.filter(user=user).values_list("issue_id", flat=True)
    )
    issues = list(
        Issue.objects
        .filter(title=current_issue.title)
        .order_by("date_publication", "issue_number")
        .values_list("id", flat=True)
    )
    for issue_id in issues:
        if issue_id not in read_issue_ids:
            try:
                nxt = Issue.objects.select_related("title", "title__publisher").get(pk=issue_id)
                return {
                    "id":            nxt.pk,
                    "title_name":    nxt.title.name,
                    "issue_number":  nxt.issue_number or "",
                    "name":          nxt.name,
                    "publisher":     nxt.title.publisher.name if nxt.title.publisher else "",
                    "date":          nxt.date_publication.strftime("%b/%Y") if nxt.date_publication else "",
                    "image_url":     nxt.image.url if nxt.image else None,
                    "in_collection": CollectionItem.objects.filter(issue=nxt, user=user).exists(),
                    "type_id":       nxt.title.type_id,
                }
            except Issue.DoesNotExist:
                pass
    return None


def _icontains_normalized(field: str, q: str) -> Q:
    """
    Busca insensível a acentos usando unaccent do PostgreSQL.
    Requer: extensão unaccent no banco + django.contrib.postgres no INSTALLED_APPS.
    Fallback: busca dupla (com e sem acento normalizado via Python).
    """
    q_norm = _normalize(q)
    try:
        from django.contrib.postgres.lookups import Unaccent
        # unaccent__icontains: remove acentos de ambos os lados antes de comparar
        return (
            Q(**{f"{field}__unaccent__icontains": q})
        )
    except Exception:
        # Fallback sem unaccent
        if q_norm == q.lower():
            return Q(**{f"{field}__icontains": q})
        return Q(**{f"{field}__icontains": q}) | Q(**{f"{field}__icontains": q_norm})


def _search_issues(q: str, type_id: int, user):
    """
    Busca no acervo.

    QUADRINHOS / REVISTAS (type_id 1 ou 3):
      - Com '#'  → busca edições por título + número. Retorna issues ordenadas
                   por data DESC (mais recentes primeiro).
      - Sem '#'  → busca títulos por nome ou editora. Retorna um card por
                   título: capa da edição mais recente, link para title_detail.
                   Cards sem toggles de coleção/lido.

    LIVROS (type_id 2):
      - Sempre busca edições (sem sintaxe #).
      - Campos: nome da edição, nome do título, editora, autor.
      - Ordem alfabética pelo nome da edição.
    """
    if not q:
        return [], False  # (resultados, is_title_search)

    q_norm = _normalize(q)

    # ── LIVROS: busca sempre por edição ──────────────────────────────────────
    if type_id == 2:
        filters = (
            _icontains_normalized("name", q)
            | _icontains_normalized("title__name", q)
            | _icontains_normalized("title__publisher__name", q)
            | _icontains_normalized("authors__name", q)
        )
        issues = list(
            Issue.objects
            .filter(Q(title__type_id=type_id) & filters)
            .select_related("title", "title__publisher", "title__type")
            .prefetch_related("authors")
            # Ordena por título primeiro (agrupa a série), depois por volume crescente
            .order_by("title__name", "issue_number", "name")
            .distinct()
        )
        return issues, False  # is_title_search=False → mostra toggles

    # ── QUADRINHOS / REVISTAS ────────────────────────────────────────────────

    if "#" in q:
        # Busca por edição específica
        parts       = q.split("#", 1)
        title_part  = parts[0].strip()
        number_part = parts[1].strip()
        filters = Q(title__type_id=type_id)
        if title_part:
            filters &= (
                _icontains_normalized("title__name", title_part)
            )
        if number_part:
            filters &= Q(issue_number__icontains=number_part)
        issues = list(
            Issue.objects
            .filter(filters)
            .select_related("title", "title__publisher", "title__type")
            .prefetch_related("authors")
            .order_by("-date_publication", "title__name", "issue_number")
            .distinct()
        )
        return issues, False  # is_title_search=False → mostra toggles

    # Busca por título — retorna um card por título
    title_filters = (
        Q(type_id=type_id) & _icontains_normalized("name", q)
    ) | (
        Q(type_id=type_id) & _icontains_normalized("publisher__name", q)
    )

    titles = (
        Title.objects
        .filter(title_filters)
        .distinct()
        .order_by("name")
    )

    # Para cada título, pega a edição mais recente para usar como capa
    results = []
    for title in titles:
        latest_issue = (
            Issue.objects
            .filter(title=title)
            .order_by("-date_publication", "-id")
            .select_related("title", "title__publisher")
            .first()
        )
        if latest_issue:
            results.append(latest_issue)

    return results, True  # is_title_search=True → sem toggles, link para title_detail


# ── Views ─────────────────────────────────────────────────────────────────────

@login_required
def issue_list(request, type_id: int, type_label: str):
    user = request.user
    q    = request.GET.get("q", "").strip()
    slug = _type_slug(type_id)

    is_title_search = False

    if q:
        issues, is_title_search = _search_issues(q, type_id, user)
        is_search = True
    else:
        next_issue_ids = _next_issues_for_user(user, type_id)
        issues = list(
            Issue.objects
            .filter(pk__in=next_issue_ids)
            .select_related("title", "title__publisher", "title__type")
            .order_by("date_publication", "title__name", "issue_number")
            .prefetch_related("authors")
        ) if next_issue_ids else []
        is_search = False

    collected_ids = set(
        CollectionItem.objects.filter(user=user).values_list("issue_id", flat=True)
    )
    read_ids = set(
        ReadItem.objects.filter(user=user).values_list("issue_id", flat=True)
    )

    context = _admin_context(request)
    context.update({
        "type_label":      type_label,
        "type_id":         type_id,
        "slug":            slug,
        "issues":          issues,
        "total":           len(issues),
        "collected_ids":   collected_ids,
        "read_ids":        read_ids,
        "q":               q,
        "is_search":       is_search,
        "is_title_search": is_title_search,
    })
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

    sibling_ids = _ordered_issues_for_title(issue.title_id)
    try:
        current_index = sibling_ids.index(issue_id)
    except ValueError:
        current_index = 0

    total_siblings = len(sibling_ids)
    slug = _type_slug(type_id)

    first_id = sibling_ids[0]                 if total_siblings > 0 else None
    prev_id  = sibling_ids[current_index - 1] if current_index > 0 else None
    next_id  = sibling_ids[current_index + 1] if current_index < total_siblings - 1 else None
    last_id  = sibling_ids[-1]                if total_siblings > 0 else None

    nav = {
        "first_url": f"/{slug}/{first_id}/" if first_id and first_id != issue_id else None,
        "prev_url":  f"/{slug}/{prev_id}/"  if prev_id else None,
        "next_url":  f"/{slug}/{next_id}/"  if next_id else None,
        "last_url":  f"/{slug}/{last_id}/"  if last_id and last_id != issue_id else None,
        "grid_url":  f"/{slug}/titulo/{issue.title_id}/",
        "position":  f"{current_index + 1} / {total_siblings}",
    }

    collection_item = CollectionItem.objects.filter(issue=issue, user=user).first()
    is_read = ReadItem.objects.filter(issue=issue, user=user).exists()

    context = _admin_context(request)
    context.update({
        "issue":           issue,
        "title":           issue.title,
        "type_label":      type_label,
        "type_id":         type_id,
        "slug":            slug,
        "nav":             nav,
        "collection_item": collection_item,
        "in_collection":   collection_item is not None,
        "is_read":         is_read,
        "show_format":     type_id == 1,
        "show_isbn":       type_id == 2,
        "show_authors":    type_id == 2,
        "show_genre":      type_id == 2,
    })
    return render(request, "core/issue_detail.html", context)


@login_required
def title_detail(request, title_id: int, type_id: int, type_label: str, slug: str):
    title = get_object_or_404(Title, pk=title_id, type_id=type_id)
    user = request.user

    issues = (
        Issue.objects.filter(title=title)
        .prefetch_related("authors")
        .order_by("-date_publication", "-id")
    )

    collected_ids = set(
        CollectionItem.objects.filter(user=user).values_list("issue_id", flat=True)
    )
    read_ids = set(
        ReadItem.objects.filter(user=user).values_list("issue_id", flat=True)
    )
    in_reading_list = ReadingList.objects.filter(user=user, title=title).exists()

    context = _admin_context(request)
    context.update({
        "title":           title,
        "type_label":      type_label,
        "type_id":         type_id,
        "slug":            slug,
        "issues":          issues,
        "total":           issues.count(),
        "collected_ids":   collected_ids,
        "read_ids":        read_ids,
        "in_reading_list": in_reading_list,
    })
    return render(request, "core/title_detail.html", context)


@login_required
@require_POST
def toggle_reading_list(request, title_id: int):
    title = get_object_or_404(Title, pk=title_id)
    user = request.user
    item, created = ReadingList.objects.get_or_create(title=title, user=user)
    if not created:
        item.delete()
        return JsonResponse({"status": "removed"})
    return JsonResponse({"status": "added"})


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
def toggle_format(request, issue_id: int):
    issue = get_object_or_404(Issue, pk=issue_id)
    user  = request.user

    item = CollectionItem.objects.filter(issue=issue, user=user).first()
    if not item:
        return JsonResponse({"status": "error", "message": "Não está na coleção"}, status=400)

    body  = json.loads(request.body or "{}")
    fmt   = body.get("format")
    value = body.get("active", True)

    if fmt == "physical":
        item.has_physical = value
    elif fmt == "digital":
        item.has_digital = value
    else:
        return JsonResponse({"status": "error", "message": "Formato inválido"}, status=400)

    item.save()
    return JsonResponse({
        "status":       "ok",
        "value":        value,
        "has_physical": item.has_physical,
        "has_digital":  item.has_digital,
    })


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

    # Auto-adiciona o título à lista de leitura se ainda não estiver
    ReadingList.objects.get_or_create(title=issue.title, user=user)

    next_data = _get_next_issue_data(user, issue)
    return JsonResponse({"status": "added", "next": next_data})


@login_required
def sortear_livro(request):
    user = request.user
    next_ids = _next_issues_for_user(user, type_id=2)
    if not next_ids:
        return redirect("livros")
    escolhido = random.choice(next_ids)
    return redirect("livros_detail", issue_id=escolhido)