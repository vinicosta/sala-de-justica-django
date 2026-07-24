# core/forms.py

from django import forms
from .models import Issue, Title, Author, Publisher, Periodicity, Format, Genre, Subgenre, Type

MONTH_CHOICES = [("", "Mês")] + [
    ("01", "Janeiro"), ("02", "Fevereiro"), ("03", "Março"),
    ("04", "Abril"),   ("05", "Maio"),      ("06", "Junho"),
    ("07", "Julho"),   ("08", "Agosto"),    ("09", "Setembro"),
    ("10", "Outubro"), ("11", "Novembro"),  ("12", "Dezembro"),
]


class IssueFullForm(forms.Form):
    """Form completo — cria Title + Issue juntos (vindo da lista geral)."""

    # ── Dados do Title ────────────────────────────────────────────────────
    title_name = forms.CharField(
        label="Nome do título",
        max_length=255,
        widget=forms.TextInput(attrs={
            "class": "slj-input",
            "placeholder": "Ex: Flash Comics (1940)",
            "autofocus": True,
        }),
    )
    publisher_name = forms.CharField(
        label="Editora",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "slj-input",
            "placeholder": "Digite para filtrar…",
            "list": "list-publishers",
            "autocomplete": "off",
        }),
    )
    periodicity_name = forms.CharField(
        label="Periodicidade",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "slj-input",
            "placeholder": "Digite para filtrar…",
            "list": "list-periodicities",
            "autocomplete": "off",
        }),
    )
    genre_name = forms.CharField(
        label="Gênero",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "slj-input",
            "placeholder": "Digite para filtrar…",
            "list": "list-genres",
            "autocomplete": "off",
        }),
    )
    format_name = forms.CharField(
        label="Formato",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "slj-input",
            "placeholder": "Digite para filtrar…",
            "list": "list-formats",
            "autocomplete": "off",
        }),
    )
    subgenre_name = forms.CharField(
        label="Subgênero",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "slj-input",
            "placeholder": "Digite para filtrar…",
            "list": "list-subgenres",
            "autocomplete": "off",
        }),
    )

    # ── Dados da Issue ────────────────────────────────────────────────────
    issue_number = forms.CharField(
        label="Nº da edição",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={"class": "slj-input", "placeholder": "Ex: 42, 12A"}),
    )
    pub_month = forms.ChoiceField(
        label="Mês",
        choices=MONTH_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "slj-select"}),
    )
    pub_year = forms.IntegerField(
        label="Ano",
        required=False,
        widget=forms.NumberInput(attrs={
            "class": "slj-input",
            "placeholder": "Ex: 1940",
            "min": "1900",
            "max": "2099",
        }),
    )
    name = forms.CharField(
        label="Nome da edição",
        max_length=255,
        widget=forms.TextInput(attrs={"class": "slj-input", "placeholder": "Nome/título da edição"}),
    )
    subtitle = forms.CharField(
        label="Subtítulo",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "slj-input", "placeholder": "Subtítulo (opcional)"}),
    )
    number_pages = forms.IntegerField(
        label="Nº de páginas",
        required=False,
        widget=forms.NumberInput(attrs={"class": "slj-input", "placeholder": "Ex: 32"}),
    )
    isbn = forms.CharField(
        label="ISBN",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={"class": "slj-input", "placeholder": "ISBN"}),
    )
    original_content = forms.CharField(
        label="Conteúdo original",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "slj-input",
            "placeholder": "Ex: Nightwing (2016) 101-105",
        }),
    )
    synopsis = forms.CharField(
        label="Sinopse",
        required=False,
        widget=forms.Textarea(attrs={"class": "slj-textarea", "rows": 4, "placeholder": "Sinopse (opcional)"}),
    )
    # Campo hidden preenchido pelo JS após upload assíncrono da capa
    authors_names = forms.CharField(required=False, widget=forms.HiddenInput())
    cover_path = forms.CharField(required=False, widget=forms.HiddenInput())


class IssueCompactForm(forms.Form):
    """Form compacto — cria Issue para um Title já existente (vindo do title_detail)."""

    issue_number = forms.CharField(
        label="Nº da edição",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={"class": "slj-input"}),
    )
    pub_month = forms.ChoiceField(
        label="Mês",
        choices=MONTH_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "slj-select"}),
    )
    pub_year = forms.IntegerField(
        label="Ano",
        required=False,
        widget=forms.NumberInput(attrs={
            "class": "slj-input",
            "min": "1900",
            "max": "2099",
        }),
    )
    name = forms.CharField(
        label="Nome da edição",
        max_length=255,
        widget=forms.TextInput(attrs={"class": "slj-input"}),
    )
    subtitle = forms.CharField(
        label="Subtítulo",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "slj-input"}),
    )
    number_pages = forms.IntegerField(
        label="Nº de páginas",
        required=False,
        widget=forms.NumberInput(attrs={"class": "slj-input"}),
    )
    isbn = forms.CharField(
        label="ISBN",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={"class": "slj-input"}),
    )
    original_content = forms.CharField(
        label="Conteúdo original",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "slj-input"}),
    )
    synopsis = forms.CharField(
        label="Sinopse",
        required=False,
        widget=forms.Textarea(attrs={"class": "slj-textarea", "rows": 4}),
    )
    authors_names = forms.CharField(required=False, widget=forms.HiddenInput())
    cover_path = forms.CharField(required=False, widget=forms.HiddenInput())

class IssueEditForm(forms.Form):
    """Form de edição de Issue existente."""

    issue_number = forms.CharField(
        label="Nº da edição",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={"class": "slj-input", "autocomplete": "off"}),
    )
    pub_month = forms.ChoiceField(
        label="Mês",
        choices=MONTH_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "slj-select"}),
    )
    pub_year = forms.IntegerField(
        label="Ano",
        required=False,
        widget=forms.NumberInput(attrs={
            "class": "slj-input",
            "min": "1900",
            "max": "2099",
        }),
    )
    name = forms.CharField(
        label="Nome da edição",
        max_length=255,
        widget=forms.TextInput(attrs={"class": "slj-input", "autocomplete": "off"}),
    )
    subtitle = forms.CharField(
        label="Subtítulo",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "slj-input", "autocomplete": "off"}),
    )
    number_pages = forms.IntegerField(
        label="Nº de páginas",
        required=False,
        widget=forms.NumberInput(attrs={"class": "slj-input"}),
    )
    isbn = forms.CharField(
        label="ISBN",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={"class": "slj-input", "autocomplete": "off"}),
    )
    original_content = forms.CharField(
        label="Conteúdo original",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "slj-input", "autocomplete": "off"}),
    )
    synopsis = forms.CharField(
        label="Sinopse",
        required=False,
        widget=forms.Textarea(attrs={"class": "slj-textarea", "autocomplete": "off", "rows": 4}),
    )
    authors_names = forms.CharField(required=False, widget=forms.HiddenInput())
    cover_path = forms.CharField(required=False, widget=forms.HiddenInput())
    clear_cover = forms.BooleanField(required=False, widget=forms.HiddenInput())

class TitleEditForm(forms.Form):
    """Form de edição dos dados de um Title existente (sem tipo, gênero/subgênero, status/origin)."""

    name = forms.CharField(
        label="Nome do título",
        max_length=255,
        widget=forms.TextInput(attrs={"class": "slj-input", "autocomplete": "off"}),
    )
    publisher_name = forms.CharField(
        label="Editora",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "slj-input",
            "placeholder": "Digite para filtrar…",
            "list": "list-publishers",
            "autocomplete": "off",
        }),
    )
    periodicity_name = forms.CharField(
        label="Periodicidade",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "slj-input",
            "placeholder": "Digite para filtrar…",
            "list": "list-periodicities",
            "autocomplete": "off",
        }),
    )
    format_name = forms.CharField(
        label="Formato",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "slj-input",
            "placeholder": "Digite para filtrar…",
            "list": "list-formats",
            "autocomplete": "off",
        }),
    )


class AuthorForm(forms.Form):
    """Form de criação/edição de Autor — usado nas telas custom de cadastro."""

    name = forms.CharField(
        label="Nome do autor",
        max_length=255,
        widget=forms.TextInput(attrs={
            "class": "slj-input",
            "placeholder": "Nome completo do autor",
            "autocomplete": "off",
            "autofocus": True,
        }),
    )


class PublisherForm(forms.Form):
    """Form de criação/edição de Editora — usado nas telas custom de cadastro."""

    name = forms.CharField(
        label="Nome da editora",
        max_length=255,
        widget=forms.TextInput(attrs={
            "class": "slj-input",
            "placeholder": "Nome da editora",
            "autocomplete": "off",
            "autofocus": True,
        }),
    )


class FormatForm(forms.Form):
    """Form de criação/edição de Formato — usado nas telas custom de cadastro."""

    name = forms.CharField(
        label="Nome do formato",
        max_length=255,
        widget=forms.TextInput(attrs={
            "class": "slj-input",
            "placeholder": "Ex: Capa dura, Encadernado, Digital",
            "autocomplete": "off",
            "autofocus": True,
        }),
    )
    type = forms.ModelChoiceField(
        label="Tipo",
        queryset=Type.objects.order_by("name"),
        empty_label=None,
        widget=forms.Select(attrs={"class": "slj-select"}),
    )


class GenreForm(forms.Form):
    """Form de criação/edição de Gênero — usado nas telas custom de cadastro."""

    name = forms.CharField(
        label="Nome do gênero",
        max_length=255,
        widget=forms.TextInput(attrs={
            "class": "slj-input",
            "placeholder": "Ex: Super-heróis, Terror, Fantasia",
            "autocomplete": "off",
            "autofocus": True,
        }),
    )


class SubgenreForm(forms.Form):
    """Form de criação/edição de Subgênero — usado nas telas custom de cadastro."""

    name = forms.CharField(
        label="Nome do subgênero",
        max_length=255,
        widget=forms.TextInput(attrs={
            "class": "slj-input",
            "placeholder": "Ex: Vigilantes urbanos, Sword and sorcery",
            "autocomplete": "off",
            "autofocus": True,
        }),
    )
    genre = forms.ModelChoiceField(
        label="Gênero",
        queryset=Genre.objects.order_by("name"),
        empty_label=None,
        widget=forms.Select(attrs={"class": "slj-select"}),
    )


class PeriodicityForm(forms.Form):
    """Form de criação/edição de Periodicidade — usado nas telas custom de cadastro."""

    name = forms.CharField(
        label="Nome",
        max_length=255,
        widget=forms.TextInput(attrs={
            "class": "slj-input",
            "placeholder": "Ex: Mensal, Bimestral, Quinzenal",
            "autocomplete": "off",
            "autofocus": True,
        }),
    )
    date_interval_number = forms.IntegerField(
        label="A cada",
        min_value=1,
        widget=forms.NumberInput(attrs={
            "class": "slj-input",
            "min": "1",
        }),
    )
    date_interval = forms.ChoiceField(
        label="Unidade",
        choices=Periodicity.INTERVAL_CHOICES,
        widget=forms.Select(attrs={"class": "slj-select"}),
    )
