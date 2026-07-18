# core/models.py
# Arquivo completo — substitui o models.py atual

from django.db import models
from django.contrib.auth.models import User

import unicodedata
import re

def issue_cover_path(instance, filename):
    type_map = {1: "comics", 2: "books", 3: "magazines"}
    type_folder = type_map.get(instance.title.type_id, "others")

    title_name = instance.title.name
    normalized = unicodedata.normalize('NFKD', title_name)
    normalized = normalized.encode('ascii', 'ignore').decode('ascii')
    normalized = re.sub(r'\s+', '_', normalized).lower()
    prefix = normalized[:3]

    return f"covers/{type_folder}/{prefix}/{filename}"


class Type(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Tipo"
        verbose_name_plural = "Tipos"

    def __str__(self):
        return self.name


class Publisher(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Editora"
        verbose_name_plural = "Editoras"

    def __str__(self):
        return self.name


class Periodicity(models.Model):
    INTERVAL_CHOICES = [
        ("day", "Dia(s)"),
        ("week", "Semana(s)"),
        ("month", "Mês(es)"),
        ("year", "Ano(s)"),
    ]

    name = models.CharField(max_length=255)
    date_interval = models.CharField(max_length=10, choices=INTERVAL_CHOICES)
    date_interval_number = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Periodicidade"
        verbose_name_plural = "Periodicidades"

    def __str__(self):
        return self.name


class Format(models.Model):
    name = models.CharField(max_length=255)
    type = models.ForeignKey(
        Type, on_delete=models.CASCADE, related_name="formats"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["type", "name"]
        verbose_name = "Formato"
        verbose_name_plural = "Formatos"

    def __str__(self):
        return f"{self.type.name} › {self.name}"


class Genre(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Gênero"
        verbose_name_plural = "Gêneros"

    def __str__(self):
        return self.name


class Subgenre(models.Model):
    name = models.CharField(max_length=255)
    genre = models.ForeignKey(
        Genre, on_delete=models.CASCADE, related_name="subgenres"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["genre", "name"]
        verbose_name = "Subgênero"
        verbose_name_plural = "Subgêneros"

    def __str__(self):
        return f"{self.genre.name} › {self.name}"


class Author(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Autor"
        verbose_name_plural = "Autores"

    def __str__(self):
        return self.name


class Title(models.Model):
    STATUS_CHOICES = [
        ("ongoing", "Em Andamento"),
        ("finished", "Encerrada"),
        ("paused", "Pausada"),
        ("miniseries", "Minissérie"),
    ]

    ORIGIN_CHOICES = [
        ("national", "Nacional"),
        ("international", "Internacional"),
    ]

    name = models.CharField(max_length=255)
    type = models.ForeignKey(
        Type, on_delete=models.PROTECT, related_name="titles"
    )
    publisher = models.ForeignKey(
        Publisher, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="titles"
    )
    periodicity = models.ForeignKey(
        Periodicity, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="titles"
    )
    format = models.ForeignKey(
        Format, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="titles"
    )
    genre = models.ForeignKey(
        Genre, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="titles"
    )
    subgenre = models.ForeignKey(
        Subgenre, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="titles"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        null=True, blank=True
    )
    origin = models.CharField(
        max_length=20, choices=ORIGIN_CHOICES,
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Título"
        verbose_name_plural = "Títulos"

    def __str__(self):
        return self.name


class Issue(models.Model):
    title = models.ForeignKey(
        Title, on_delete=models.CASCADE, related_name="issues"
    )
    name = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, null=True, default="")
    issue_number = models.CharField(max_length=50, blank=True, null=True, default="")
    date_publication = models.DateField(null=True, blank=True)
    is_estimated = models.BooleanField(
        default=False,
        help_text="Data de publicação estimada automaticamente pela periodicidade"
    )
    number_pages = models.PositiveIntegerField(null=True, blank=True)
    isbn = models.CharField(max_length=50, blank=True, null=True, default="")
    original_content = models.CharField(
        max_length=255, blank=True, null=True, default="",
        help_text="Edição original em que o conteúdo foi publicado (ex: Nightwing (2016) 101-105). Apenas quadrinhos."
    )
    synopsis = models.TextField(blank=True, null=True, default="")
    image = models.ImageField(upload_to=issue_cover_path, null=True, blank=True, max_length=255)
    authors = models.ManyToManyField(
        Author, blank=True, related_name="issues"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title", "issue_number"]
        verbose_name = "Edição"
        verbose_name_plural = "Edições"

    def __str__(self):
        if self.issue_number:
            return f"{self.title.name} #{self.issue_number} — {self.name}"
        return f"{self.title.name} — {self.name}"


class CollectionItem(models.Model):
    issue = models.ForeignKey(
        Issue, on_delete=models.CASCADE, related_name="collection_items"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="collection_items"
    )
    added_date = models.DateField(null=True, blank=True)
    has_physical = models.BooleanField(
        default=False,
        help_text="Possui a versão física",
    )
    has_digital = models.BooleanField(
        default=False,
        help_text="Possui a versão digital",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("issue", "user")
        verbose_name = "Item do Acervo"
        verbose_name_plural = "Acervo"

    def __str__(self):
        flags = []
        if self.has_physical:
            flags.append("físico")
        if self.has_digital:
            flags.append("digital")
        suffix = f" ({', '.join(flags)})" if flags else ""
        return f"{self.user.username} › {self.issue}{suffix}"


class ReadItem(models.Model):
    issue = models.ForeignKey(
        Issue, on_delete=models.CASCADE, related_name="read_items"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="read_items"
    )
    read_date = models.DateField(null=True, blank=True)
    is_reread = models.BooleanField(
        default=False,
        help_text="Marque se esta é uma releitura"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("issue", "user", "is_reread")
        verbose_name = "Leitura"
        verbose_name_plural = "Leituras"

    def __str__(self):
        reread = " (releitura)" if self.is_reread else ""
        return f"{self.user.username} › {self.issue}{reread}"


class ReadingList(models.Model):
    title = models.ForeignKey(
        Title, on_delete=models.CASCADE, related_name="reading_list_items"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reading_list_items"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("title", "user")
        verbose_name = "Lista de Leitura"
        verbose_name_plural = "Lista de Leitura"

    def __str__(self):
        return f"{self.user.username} › {self.title}"