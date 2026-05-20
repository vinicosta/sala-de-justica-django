# core/views.py

import json
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .models import CollectionItem, Issue, ReadItem, ReadingList


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


@staff_member_required
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


@staff_member_required
@require_POST
def toggle_collection(request, issue_id: int):
    issue = get_object_or_404(Issue, pk=issue_id)
    user  = request.user

    item, created = CollectionItem.objects.get_or_create(
        issue=issue, user=user,
        defaults={"is_digital": False},
    )

    if not created:
        body = json.loads(request.body or "{}")
        if body.get("confirm"):
            item.delete()
            return JsonResponse({"status": "removed"})
        return JsonResponse({"status": "confirm_needed"})

    return JsonResponse({"status": "added"})


@staff_member_required
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