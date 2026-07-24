# core/gap_detection.py

import re
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from .models import Issue, Periodicity


def _extract_base_number(issue_number: str) -> int | None:
    """Extrai a parte numérica inicial de um issue_number."""
    if not issue_number:
        return None
    m = re.match(r'^(\d+)', issue_number.strip())
    if not m:
        return None
    return int(m.group(1))


def _calc_date(anchor_date: date, steps: int, periodicity: Periodicity | None) -> date | None:
    """
    Calcula a data estimada somando `steps` intervalos a partir de anchor_date.
    Se não houver periodicidade, usa 30 dias como default.

    Aceita tanto o formato abreviado ("d", "w", "m", "y" — usado nos dados
    migrados do MySQL/Laravel) quanto o formato por extenso ("day", "week",
    "month", "year" — usado pelo cadastro novo de Periodicidades), no mesmo
    padrão já adotado em views.py para a sugestão de data da "Nova edição".
    """
    if anchor_date is None:
        return None

    if periodicity is None:
        return anchor_date + timedelta(days=30 * steps)

    interval = (periodicity.date_interval or "").strip().lower()
    n = periodicity.date_interval_number * steps

    if interval in ("day", "d"):
        return anchor_date + timedelta(days=n)
    elif interval in ("week", "w"):
        return anchor_date + timedelta(weeks=n)
    elif interval in ("month", "m"):
        return anchor_date + relativedelta(months=n)
    elif interval in ("year", "y"):
        return anchor_date + relativedelta(years=n)

    return anchor_date + timedelta(days=30 * steps)


def fill_gaps(title) -> list:
    """
    Detecta e preenche lacunas numéricas nas edições de um título.
    Retorna lista das edições criadas.
    """
    periodicity = title.periodicity

    # Todas as edições com número base numérico, ordenadas
    issues = list(
        Issue.objects.filter(title=title)
        .exclude(issue_number__isnull=True)
        .exclude(issue_number="")
        .order_by("date_publication", "id")
    )

    # Mapeia número base → maior issue_number visto (para lidar com variantes)
    # e também guarda a edição com data real mais recente por número base
    base_map: dict[int, Issue] = {}  # base_num → issue (para referência de data)

    for issue in issues:
        base = _extract_base_number(issue.issue_number)
        if base is None:
            continue
        # Guarda a edição com data real mais recente para cada número base
        existing = base_map.get(base)
        if existing is None:
            base_map[base] = issue
        elif not existing.is_estimated and issue.is_estimated:
            pass  # mantém a real
        elif issue.date_publication and (
            not existing.date_publication or
            issue.date_publication > existing.date_publication
        ):
            base_map[base] = issue

    if not base_map:
        return []

    existing_bases = set(base_map.keys())
    min_base = min(existing_bases)
    max_base = max(existing_bases)

    # Gaps = números entre min e max que não existem
    gaps = sorted(set(range(min_base, max_base + 1)) - existing_bases)

    if not gaps:
        return []

    # Encontra a âncora: edição com data real mais recente, com base < gap
    def find_anchor(gap_num: int) -> tuple[date | None, int]:
        """Retorna (anchor_date, anchor_base) — base imediatamente anterior ao gap com data real."""
        candidates = [
            (base, iss) for base, iss in base_map.items()
            if base < gap_num and iss.date_publication and not iss.is_estimated
        ]
        if not candidates:
            # Fallback: qualquer base anterior com data
            candidates = [
                (base, iss) for base, iss in base_map.items()
                if base < gap_num and iss.date_publication
            ]
        if not candidates:
            return None, gap_num - 1
        anchor_base, anchor_issue = max(candidates, key=lambda x: x[0])
        return anchor_issue.date_publication, anchor_base

    created = []

    for gap_num in gaps:
        anchor_date, anchor_base = find_anchor(gap_num)
        steps = gap_num - anchor_base
        estimated_date = _calc_date(anchor_date, steps, periodicity)

        issue = Issue(
            title=title,
            issue_number=str(gap_num),
            name=title.name,
            is_estimated=True,
            date_publication=estimated_date,
        )
        issue.save()
        # Adiciona ao base_map para que gaps subsequentes usem como âncora se necessário
        base_map[gap_num] = issue
        created.append(issue)

    return created