# core/views.py

import json, random, unicodedata, re
from datetime import date

from django.contrib.admin import site as admin_site
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST

from .forms import IssueCompactForm, IssueFullForm
from .models import (
    Author, CollectionItem, Format, Genre, Issue, Periodicity,
    Publisher, ReadItem, ReadingList, Subgenre, Title,
)
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
    q_norm = _normalize(q)
    try:
        from django.contrib.postgres.lookups import Unaccent
        return Q(**{f"{field}__unaccent__icontains": q})
    except Exception:
        if q_norm == q.lower():
            return Q(**{f"{field}__icontains": q})
        return Q(**{f"{field}__icontains": q}) | Q(**{f"{field}__icontains": q_norm})


def _search_issues(q: str, type_id: int, user):
    if not q:
        return [], False

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
            .order_by("title__name", "issue_number", "name")
            .distinct()
        )
        return issues, False

    if "#" in q:
        parts       = q.split("#", 1)
        title_part  = parts[0].strip()
        number_part = parts[1].strip()
        filters = Q(title__type_id=type_id)
        if title_part:
            filters &= _icontains_normalized("title__name", title_part)
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
        return issues, False

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

    return results, True


def _build_date(month: str, year) -> date | None:
    if month and year:
        try:
            return date(int(year), int(month), 1)
        except (ValueError, TypeError):
            pass
    return None


def _resolve_fk(model, name_field: str, value: str):
    if not value or not value.strip():
        return None
    return model.objects.filter(**{f"{name_field}__iexact": value.strip()}).first()


def _resolve_authors(names_str: str) -> list:
    """
    Recebe nomes separados por '|' (vindos do campo hidden authors_names),
    busca cada autor por nome (case-insensitive) e cria os que não existirem.
    Retorna a lista de objetos Author.
    """
    authors = []
    for raw in (names_str or "").split("|"):
        name = raw.strip()
        if not name:
            continue
        author = Author.objects.filter(name__iexact=name).first()
        if not author:
            author = Author.objects.create(name=name)
        authors.append(author)
    return authors


def _next_issue_defaults(title: Title) -> dict:
    from dateutil.relativedelta import relativedelta

    type_id = title.type_id  # 1=quadrinhos, 2=livros, 3=revistas
    is_book = type_id == 2

    if is_book:
        last = (
            Issue.objects
            .filter(title=title, is_estimated=False)
            .order_by("-id")
            .first()
        )
        last_with_num = (
            Issue.objects
            .filter(title=title, is_estimated=False)
            .exclude(issue_number="")
            .exclude(issue_number=None)
            .order_by("-id")
            .first()
        )
        if last_with_num:
            last = last_with_num
    else:
        last = (
            Issue.objects
            .filter(title=title, is_estimated=False)
            .exclude(date_publication=None)
            .order_by("-date_publication", "-issue_number")
            .first()
        )
        if not last:
            last = (
                Issue.objects
                .filter(title=title, is_estimated=False)
                .order_by("-id")
                .first()
            )

    defaults = {"name": last.name if last else title.name}

    if is_book and last:
        defaults["authors_names"] = "|".join(
            last.authors.order_by("name").values_list("name", flat=True)
        )

    if is_book:
        if last and last.issue_number:
            try:
                m = re.match(r"(\d+)", last.issue_number)
                if m:
                    defaults["issue_number"] = str(int(m.group(1)) + 1)
                else:
                    defaults["issue_number"] = "2"
            except (ValueError, AttributeError):
                defaults["issue_number"] = "2"
        else:
            defaults["issue_number"] = "2"
    else:
        if last and last.issue_number:
            try:
                m = re.match(r"(\d+)", last.issue_number)
                if m:
                    defaults["issue_number"] = str(int(m.group(1)) + 1)
            except (ValueError, AttributeError):
                pass

        if last and last.date_publication:
            # Determina o delta pela periodicidade (aceita formato longo e abreviado)
            # Fallback: mensal se não tiver periodicidade definida
            delta = relativedelta(months=1)  # default mensal
            if title.periodicity:
                p = title.periodicity
                n = p.date_interval_number or 1
                interval = (p.date_interval or "").lower()
                delta_map = {
                    "day":   relativedelta(days=n),
                    "d":     relativedelta(days=n),
                    "week":  relativedelta(weeks=n),
                    "w":     relativedelta(weeks=n),
                    "month": relativedelta(months=n),
                    "m":     relativedelta(months=n),
                    "year":  relativedelta(years=n),
                    "y":     relativedelta(years=n),
                }
                delta = delta_map.get(interval, relativedelta(months=1))
            next_date = last.date_publication + delta
            defaults["pub_month"] = next_date.strftime("%m")
            defaults["pub_year"]  = next_date.year
        elif last and last.date_publication:
            defaults["pub_month"] = last.date_publication.strftime("%m")
            defaults["pub_year"]  = last.date_publication.year

    return defaults


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
        "show_original_content": type_id == 1,
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
def title_edit(request, title_id: int, type_id: int, type_label: str, slug: str):
    """Edição dos dados básicos de um Title existente."""
    from .forms import TitleEditForm
    title = get_object_or_404(Title, pk=title_id, type_id=type_id)
    back_url = f"/{slug}/titulo/{title.pk}/"

    # Datalists para autocomplete
    publishers    = list(Publisher.objects.order_by("name").values_list("name", flat=True))
    periodicities = list(Periodicity.objects.order_by("name").values_list("name", flat=True))
    formats       = list(Format.objects.filter(type_id=type_id).order_by("name").values_list("name", flat=True))

    if request.method == "POST":
        form = TitleEditForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            title.name        = d["name"].strip()
            title.publisher   = _resolve_fk(Publisher,   "name", d.get("publisher_name", ""))
            title.periodicity = _resolve_fk(Periodicity, "name", d.get("periodicity_name", ""))
            title.format      = _resolve_fk(Format,      "name", d.get("format_name", ""))
            title.save()
            return redirect(back_url)
    else:
        initial = {
            "name":              title.name,
            "publisher_name":    title.publisher.name if title.publisher else "",
            "periodicity_name":  title.periodicity.name if title.periodicity else "",
            "format_name":       title.format.name if title.format else "",
        }
        form = TitleEditForm(initial=initial)

    context = _admin_context(request)
    context.update({
        "form":           form,
        "title":          title,
        "type_id":        type_id,
        "type_label":     type_label,
        "slug":           slug,
        "publishers":     publishers,
        "periodicities":  periodicities,
        "formats":        formats,
        "back_url":       back_url,
        "show_periodicity": type_id != 2,
    })
    return render(request, "core/title_form.html", context)


@login_required
def issue_create(request, type_id: int, type_label: str):
    """
    Form híbrido:
    - ?title_id=X  → form compacto (title já existe, valores pré-calculados)
    - sem title_id → form completo (cria title + issue juntos)
    """
    slug      = _type_slug(type_id)
    title_id  = request.GET.get("title_id") or request.POST.get("title_id")
    title     = None
    is_compact = False

    if title_id:
        title      = get_object_or_404(Title, pk=title_id, type_id=type_id)
        is_compact = True

    # Datalists para autocomplete
    publishers    = list(Publisher.objects.order_by("name").values_list("name", flat=True))
    periodicities = list(Periodicity.objects.order_by("name").values_list("name", flat=True))
    formats       = list(Format.objects.filter(type_id=type_id).order_by("name").values_list("name", flat=True))
    subgenres     = list(Subgenre.objects.order_by("name").values_list("name", flat=True))
    authors_list  = list(Author.objects.order_by("name").values_list("name", flat=True))
    genres        = list(Genre.objects.order_by("name").values_list("name", flat=True))
    # Pares subgênero → gênero para o filtro em cascata (livros)
    subgenres_map = json.dumps([
        {"name": s.name, "genre": s.genre.name}
        for s in Subgenre.objects.select_related("genre").order_by("name")
    ])

    if request.method == "POST":
        form = IssueCompactForm(request.POST) if is_compact else IssueFullForm(request.POST)

        if form.is_valid():
            d = form.cleaned_data

            if not is_compact:
                publisher   = _resolve_fk(Publisher,   "name", d.get("publisher_name", ""))
                periodicity = _resolve_fk(Periodicity, "name", d.get("periodicity_name", "")) if type_id != 2 else None
                fmt         = _resolve_fk(Format,      "name", d.get("format_name", ""))
                genre       = _resolve_fk(Genre,       "name", d.get("genre_name", "")) if type_id == 2 else None
                subgenre    = _resolve_fk(Subgenre,    "name", d.get("subgenre_name", ""))

                title = Title.objects.create(
                    name        = d["title_name"].strip(),
                    type_id     = type_id,
                    publisher   = publisher,
                    periodicity = periodicity,
                    format      = fmt,
                    genre       = genre,
                    subgenre    = subgenre,
                )

            pub_date = _build_date(d.get("pub_month"), d.get("pub_year"))

            issue = Issue.objects.create(
                title            = title,
                name             = d["name"].strip(),
                subtitle         = d.get("subtitle", "").strip(),
                issue_number     = d.get("issue_number", "").strip(),
                date_publication = pub_date,
                number_pages     = d.get("number_pages"),
                isbn             = d.get("isbn", "").strip() if type_id == 2 else "",
                original_content = d.get("original_content", "").strip() if type_id == 1 else "",
                synopsis         = d.get("synopsis", "").strip(),
                image            = d.get("cover_path") or None,
            )

            # Autores (apenas livros)
            if type_id == 2:
                issue.authors.set(_resolve_authors(d.get("authors_names", "")))

            # Dispara fill_gaps para o título afetado
            fill_gaps(title)

            return redirect(f"/{slug}/{issue.pk}/")

    else:
        if is_compact:
            form = IssueCompactForm(initial=_next_issue_defaults(title))
        else:
            form = IssueFullForm()

    context = _admin_context(request)
    context.update({
        "form":           form,
        "type_id":        type_id,
        "type_label":     type_label,
        "slug":           slug,
        "is_compact":     is_compact,
        "title":          title,
        "title_id":       title_id or "",
        "publishers":     publishers,
        "periodicities":  periodicities,
        "formats":        formats,
        "subgenres":      subgenres,
        "authors_list":   authors_list,
        "genres":         genres,
        "subgenres_map":  subgenres_map,
        "show_isbn":      type_id == 2,
        "show_original_content": type_id == 1,
        "show_authors_field": type_id == 2,
        "back_url":       f"/{slug}/",
        "existing_cover_url": None,
        "is_edit":        False,
    })
    return render(request, "core/issue_form.html", context)


@login_required
def issue_edit(request, type_id: int, type_label: str, issue_id: int):
    from .forms import IssueEditForm
    slug  = _type_slug(type_id)
    issue = get_object_or_404(Issue, pk=issue_id, title__type_id=type_id)
    title = issue.title
    back_url = f"/{slug}/{issue.pk}/"

    if request.method == "POST":
        form = IssueEditForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            pub_date = _build_date(d.get("pub_month"), d.get("pub_year"))
            issue.name             = d["name"].strip()
            issue.subtitle         = d.get("subtitle", "").strip()
            issue.issue_number     = d.get("issue_number", "").strip()
            issue.date_publication = pub_date
            issue.number_pages     = d.get("number_pages")
            issue.synopsis         = d.get("synopsis", "").strip()
            if type_id == 2:
                issue.isbn = d.get("isbn", "").strip()
            if type_id == 1:
                issue.original_content = d.get("original_content", "").strip()
            if d.get("clear_cover"):
                issue.image = None
            elif d.get("cover_path"):
                issue.image = d["cover_path"]
            issue.save()

            # Autores (apenas livros)
            if type_id == 2:
                issue.authors.set(_resolve_authors(d.get("authors_names", "")))

            fill_gaps(title)
            return redirect(back_url)
    else:
        initial = {
            "name":             issue.name,
            "subtitle":         issue.subtitle or "",
            "issue_number":     issue.issue_number or "",
            "pub_month":        issue.date_publication.strftime("%m") if issue.date_publication else "",
            "pub_year":         issue.date_publication.year if issue.date_publication else None,
            "number_pages":     issue.number_pages,
            "isbn":             issue.isbn or "",
            "original_content": issue.original_content or "",
            "synopsis":         issue.synopsis or "",
            "authors_names":    "|".join(
                issue.authors.order_by("name").values_list("name", flat=True)
            ),
        }
        form = IssueEditForm(initial=initial)

    context = _admin_context(request)
    context.update({
        "form":                  form,
        "issue":                 issue,
        "title":                 title,
        "type_id":               type_id,
        "type_label":            type_label,
        "slug":                  slug,
        "is_edit":               True,
        "is_compact":            True,
        "title_id":              title.pk,
        "show_isbn":             type_id == 2,
        "show_original_content": type_id == 1,
        "show_issue_number":     type_id != 2,
        "show_pub_date":         type_id != 2,
        "publishers":            [],
        "periodicities":         [],
        "formats":               [],
        "subgenres":             [],
        "authors_list":          list(Author.objects.order_by("name").values_list("name", flat=True)),
        "genres":                [],
        "subgenres_map":         "[]",
        "show_authors_field":    type_id == 2,
        "back_url":              back_url,
        "existing_cover_url":    issue.image.url if issue.image else None,
    })
    return render(request, "core/issue_form.html", context)


@login_required
@require_POST
def upload_cover(request):
    """
    Recebe imagem via AJAX, salva em covers/temp/ e devolve path + URL.
    O path vai para o hidden input cover_path e é associado à Issue no submit.
    """
    file = request.FILES.get("cover")
    if not file:
        return JsonResponse({"error": "Nenhum arquivo enviado."}, status=400)

    allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed:
        return JsonResponse({"error": "Formato não suportado."}, status=400)

    path = default_storage.save(f"covers/temp/{file.name}", file)
    url  = default_storage.url(path)

    return JsonResponse({"path": path, "url": url})


# ── Ações AJAX ────────────────────────────────────────────────────────────────

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