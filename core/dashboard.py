from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDay, TruncMonth
from django.utils import timezone
from datetime import timedelta, date
import calendar
import hashlib

from core.models import CollectionItem, ReadItem, Title, Issue


def dashboard_callback(request, context):
    """
    Callback do Unfold para o dashboard principal do Sala de Justiça.
    """

    TYPE_QUADRINHOS = 1
    TYPE_LIVRO = 2
    TYPE_REVISTA = 3

    hoje = timezone.now().date()

    context["site_header"] = "Sala de Justiça / App"

    # ------------------------------------------------------------------ #
    # Cards principais — acervo por tipo
    # ------------------------------------------------------------------ #
    def acervo_count(type_id):
        return CollectionItem.objects.filter(
            issue__title__type_id=type_id
        ).count()

    context["acervo_quadrinhos"] = acervo_count(TYPE_QUADRINHOS)
    context["acervo_livros"]     = acervo_count(TYPE_LIVRO)
    context["acervo_revistas"]   = acervo_count(TYPE_REVISTA)

    # ------------------------------------------------------------------ #
    # Cards secundários
    # ------------------------------------------------------------------ #
    context["total_titulos"] = Title.objects.count()
    context["total_edicoes"] = Issue.objects.count()

    inicio_mes = hoje.replace(day=1)
    leituras_mes = ReadItem.objects.filter(
        read_date__gte=inicio_mes,
        issue__title__type_id__in=[TYPE_QUADRINHOS, TYPE_LIVRO],
    )
    context["paginas_mes"]      = leituras_mes.aggregate(total=Sum("issue__number_pages"))["total"] or 0
    context["edicoes_lidas_mes"] = leituras_mes.count()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    MESES_PT = ["", "jan", "fev", "mar", "abr", "mai", "jun",
                "jul", "ago", "set", "out", "nov", "dez"]

    def _avancar_mes(d):
        return (d.replace(day=28) + timedelta(days=4)).replace(day=1)

    def paginas_por_dia(type_ids, dias=14):
        inicio = hoje - timedelta(days=dias - 1)
        raw = (
            ReadItem.objects
            .filter(read_date__gte=inicio, issue__title__type_id__in=type_ids)
            .annotate(dia=TruncDay("read_date"))
            .values("dia")
            .annotate(total=Sum("issue__number_pages"))
            .order_by("dia")
        )
        mapa = {r["dia"]: r["total"] or 0 for r in raw}
        labels, data = [], []
        for i in range(dias):
            d = inicio + timedelta(days=i)
            labels.append(d.strftime("%d/%m"))
            data.append(mapa.get(d, 0))
        return labels, data

    def paginas_por_mes(type_ids):
        inicio = _avancar_mes(hoje.replace(day=1) - timedelta(days=365))
        raw = (
            ReadItem.objects
            .filter(read_date__gte=inicio, issue__title__type_id__in=type_ids)
            .annotate(mes=TruncMonth("read_date"))
            .values("mes")
            .annotate(total=Sum("issue__number_pages"))
            .order_by("mes")
        )
        mapa = {r["mes"]: r["total"] or 0 for r in raw}
        labels, data = [], []
        cursor = inicio
        while cursor <= hoje.replace(day=1):
            labels.append(f"{MESES_PT[cursor.month]}/{str(cursor.year)[2:]}")
            data.append(mapa.get(cursor, 0))
            cursor = _avancar_mes(cursor)
        return labels, data

    def edicoes_por_dia(type_id, dias=7):
        inicio = hoje - timedelta(days=dias - 1)
        raw = (
            ReadItem.objects
            .filter(read_date__gte=inicio, issue__title__type_id=type_id)
            .annotate(dia=TruncDay("read_date"))
            .values("dia")
            .annotate(total=Count("id"))
            .order_by("dia")
        )
        mapa = {r["dia"]: r["total"] for r in raw}
        labels, data = [], []
        for i in range(dias):
            d = inicio + timedelta(days=i)
            labels.append(d.strftime("%d/%m"))
            data.append(mapa.get(d, 0))
        return labels, data

    def edicoes_mes_corrente(type_id):
        inicio = hoje.replace(day=1)
        ultimo_dia = calendar.monthrange(hoje.year, hoje.month)[1]
        raw = (
            ReadItem.objects
            .filter(read_date__gte=inicio, issue__title__type_id=type_id)
            .annotate(dia=TruncDay("read_date"))
            .values("dia")
            .annotate(total=Count("id"))
            .order_by("dia")
        )
        mapa = {r["dia"]: r["total"] for r in raw}
        labels, data = [], []
        for i in range(ultimo_dia):
            d = inicio + timedelta(days=i)
            labels.append(str(d.day))
            data.append(mapa.get(d, 0))
        return labels, data

    def edicoes_ano_corrente(type_id):
        inicio = date(hoje.year, 1, 1)
        raw = (
            ReadItem.objects
            .filter(read_date__gte=inicio, issue__title__type_id=type_id)
            .annotate(mes=TruncMonth("read_date"))
            .values("mes")
            .annotate(total=Count("id"))
            .order_by("mes")
        )
        mapa = {r["mes"]: r["total"] for r in raw}
        labels, data = [], []
        for m in range(1, 13):
            labels.append(MESES_PT[m])
            data.append(mapa.get(date(hoje.year, m, 1), 0))
        return labels, data

    def periodo_edicoes(inicio, fim, type_id):
        """Total de edições lidas de um tipo específico num intervalo de datas."""
        return ReadItem.objects.filter(
            read_date__gte=inicio,
            read_date__lte=fim,
            issue__title__type_id=type_id,
        ).count()

    # ------------------------------------------------------------------ #
    # Páginas (quadrinhos + livros)
    # ------------------------------------------------------------------ #
    tipos_ql = [TYPE_QUADRINHOS, TYPE_LIVRO]
    context["chart_pag_dia_labels"], context["chart_pag_dia_data"] = paginas_por_dia(tipos_ql)
    context["chart_pag_mes_labels"], context["chart_pag_mes_data"] = paginas_por_mes(tipos_ql)

    # ------------------------------------------------------------------ #
    # Edições — últimos 7 dias
    # ------------------------------------------------------------------ #
    context["chart_7d_q_labels"], context["chart_7d_q_data"] = edicoes_por_dia(TYPE_QUADRINHOS)
    context["chart_7d_l_labels"], context["chart_7d_l_data"] = edicoes_por_dia(TYPE_LIVRO)

    # ------------------------------------------------------------------ #
    # Edições — mês corrente
    # ------------------------------------------------------------------ #
    context["chart_mc_q_labels"], context["chart_mc_q_data"] = edicoes_mes_corrente(TYPE_QUADRINHOS)
    context["chart_mc_l_labels"], context["chart_mc_l_data"] = edicoes_mes_corrente(TYPE_LIVRO)

    # ------------------------------------------------------------------ #
    # Edições — ano corrente
    # ------------------------------------------------------------------ #
    context["chart_ac_q_labels"], context["chart_ac_q_data"] = edicoes_ano_corrente(TYPE_QUADRINHOS)
    context["chart_ac_l_labels"], context["chart_ac_l_data"] = edicoes_ano_corrente(TYPE_LIVRO)

    # ------------------------------------------------------------------ #
    # Contadores — mês anterior x mês atual / ano anterior x ano atual
    # (separado por tipo: Quadrinhos e Livros)
    # ------------------------------------------------------------------ #
    inicio_mes_atual = hoje.replace(day=1)
    fim_mes_atual = hoje

    fim_mes_anterior = inicio_mes_atual - timedelta(days=1)
    inicio_mes_anterior = fim_mes_anterior.replace(day=1)

    context["edicoes_mes_anterior_q"] = periodo_edicoes(inicio_mes_anterior, fim_mes_anterior, TYPE_QUADRINHOS)
    context["edicoes_mes_atual_q"]    = periodo_edicoes(inicio_mes_atual, fim_mes_atual, TYPE_QUADRINHOS)
    context["edicoes_mes_anterior_l"] = periodo_edicoes(inicio_mes_anterior, fim_mes_anterior, TYPE_LIVRO)
    context["edicoes_mes_atual_l"]    = periodo_edicoes(inicio_mes_atual, fim_mes_atual, TYPE_LIVRO)

    inicio_ano_atual = date(hoje.year, 1, 1)
    fim_ano_atual = hoje

    inicio_ano_anterior = date(hoje.year - 1, 1, 1)
    fim_ano_anterior = date(hoje.year - 1, 12, 31)

    context["edicoes_ano_anterior_q"] = periodo_edicoes(inicio_ano_anterior, fim_ano_anterior, TYPE_QUADRINHOS)
    context["edicoes_ano_atual_q"]    = periodo_edicoes(inicio_ano_atual, fim_ano_atual, TYPE_QUADRINHOS)
    context["edicoes_ano_anterior_l"] = periodo_edicoes(inicio_ano_anterior, fim_ano_anterior, TYPE_LIVRO)
    context["edicoes_ano_atual_l"]    = periodo_edicoes(inicio_ano_atual, fim_ano_atual, TYPE_LIVRO)

    # ------------------------------------------------------------------ #
    # Tabela — últimas 8 leituras recentes
    # ------------------------------------------------------------------ #
    recentes = (
        ReadItem.objects
        .select_related("issue__title__type", "issue__title__publisher")
        .order_by(F("read_date").desc(nulls_last=True), "-id")[:8]
    )

    # Livros: o nome exibido depende de quantas edições o título possui.
    # Uma única edição → apenas o nome da edição.
    # Mais de uma      → "nome da edição - nome do título, vol. <número>".
    titulos_livro = {
        item.issue.title_id for item in recentes
        if item.issue.title.type_id == TYPE_LIVRO
    }
    edicoes_por_titulo = {
        r["title_id"]: r["total"]
        for r in Issue.objects
        .filter(title_id__in=titulos_livro)
        .values("title_id")
        .annotate(total=Count("id"))
    }

    leituras_recentes = []
    for item in recentes:
        issue  = item.issue
        title  = issue.title
        tipo_id = title.type_id

        if tipo_id == TYPE_QUADRINHOS:
            tipo_label, tipo_color, tipo_bg = "Q", "#1D9E75", "rgba(29,158,117,0.13)"
        elif tipo_id == TYPE_LIVRO:
            tipo_label, tipo_color, tipo_bg = "L", "#185FA5", "rgba(55,138,221,0.13)"
        else:
            tipo_label, tipo_color, tipo_bg = "R", "#993C1D", "rgba(216,90,48,0.13)"

        if tipo_id == TYPE_LIVRO:
            nome = issue.name
            if edicoes_por_titulo.get(issue.title_id, 1) > 1:
                nome = f"{nome} - {title.name}"
                if issue.issue_number:
                    nome = f"{nome}, vol. {issue.issue_number}"
            numero = ""
        else:
            nome = issue.name
            numero = issue.issue_number or ""

        leituras_recentes.append({
            "nome":       nome,
            "numero":     numero,
            "editora":    title.publisher.name if title.publisher else "—",
            "data":       item.read_date.strftime("%d/%m/%Y") if item.read_date else "—",
            "paginas":    issue.number_pages or 0,
            "capa":       issue.image.url if issue.image else None,
            "tipo_label": tipo_label,
            "tipo_color": tipo_color,
            "tipo_bg":    tipo_bg,
        })

    context["leituras_recentes"] = leituras_recentes

    context["cards_secundarios"] = [
        ("Total de títulos",       context["total_titulos"]),
        ("Total de edições",       context["total_edicoes"]),
        ("Páginas lidas este mês", context["paginas_mes"]),
        ("Edições lidas este mês", context["edicoes_lidas_mes"]),
    ]

    return context