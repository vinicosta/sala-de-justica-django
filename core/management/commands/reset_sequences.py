"""
core/management/commands/reset_sequences.py

Reseta as sequences (auto-increment) do Postgres para os models do
catálogo, após migrações que usam bulk_create com IDs explícitos
(que não avançam a sequence automaticamente).

Uso:
    docker compose exec web python manage.py reset_sequences
"""

from django.core.management.base import BaseCommand
from django.db import connection

from core.models import (
    Publisher, Genre, Subgenre, Periodicity, Format,
    Author, Title, Issue, CollectionItem, ReadItem, ReadingList
)

MODELS = [
    Publisher, Genre, Subgenre, Periodicity, Format,
    Author, Title, Issue, CollectionItem, ReadItem, ReadingList,
]


class Command(BaseCommand):
    help = 'Reseta as sequences do Postgres para os models do catálogo'

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            for model in MODELS:
                table = model._meta.db_table
                cursor.execute(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table}', 'id'),
                        COALESCE((SELECT MAX(id) FROM "{table}"), 1),
                        (SELECT MAX(id) FROM "{table}") IS NOT NULL
                    )
                    """
                )
                self.stdout.write(f'  {table}: sequence resetada')

        self.stdout.write(self.style.SUCCESS('✅ Todas as sequences resetadas'))
