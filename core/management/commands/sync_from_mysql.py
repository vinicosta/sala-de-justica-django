"""
core/management/commands/sync_from_mysql.py

Sincroniza incrementalmente o Postgres/Django com um dump mais recente
do MySQL legado (Hostgator), sem refazer a migração completa.

Pressupõe que:
- O dump novo já foi importado numa base separada dentro do mesmo
  container MySQL legado, com o nome `salade10_app_new`
  (a base original migrada continua em `salade10_app`, intocada).
- Os IDs originais do MySQL foram preservados como PK no Django
  (confirmado em migrate_from_mysql.py).

Uso:
    docker compose exec web python manage.py sync_from_mysql --dry-run
    docker compose exec web python manage.py sync_from_mysql
"""

import datetime as dt

import pymysql
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Title, Issue, CollectionItem


def to_utc_naive(value):
    """Normaliza um datetime (aware ou naive) para naive em UTC, para comparação segura."""
    if value is None:
        return None
    if timezone.is_aware(value):
        return value.astimezone(dt.timezone.utc).replace(tzinfo=None)
    return value

MYSQL_CONFIG = {
    'host': 'mysql_legacy',
    'port': 3306,
    'user': 'root',
    'password': 'legacy_root',
    'database': 'salade10_app_new',
    'charset': 'utf8mb4',
    'use_unicode': True,
    'cursorclass': pymysql.cursors.DictCursor,
}

NOW = timezone.now()


class Command(BaseCommand):
    help = 'Sincroniza incrementalmente o Django com o dump novo do MySQL legado (salade10_app_new)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria feito, sem gravar nada no banco',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        if self.dry_run:
            self.stdout.write(self.style.WARNING('🔍 Modo DRY-RUN — nada será gravado'))

        conn = pymysql.connect(**MYSQL_CONFIG)
        try:
            with conn.cursor() as c:
                c.execute("SET NAMES utf8mb4")
                c.execute("SET CHARACTER SET utf8mb4")
                c.execute("SET character_set_connection=utf8mb4")
                # CRÍTICO: o dump original foi gerado com time_zone="+00:00".
                # Sem forçar isso aqui também, o MySQL pode converter os
                # TIMESTAMPs para o timezone padrão do servidor na leitura,
                # fazendo quase todo registro parecer "alterado" na comparação.
                c.execute("SET time_zone = '+00:00'")

            self.stdout.write('🔌 Conectado ao MySQL legado (salade10_app_new)')

            with conn.cursor() as cursor:
                self.sync_titles(cursor)
                self.sync_issues(cursor)
                self.sync_collection(cursor)

            self.stdout.write(self.style.SUCCESS('✅ Sincronização concluída!'))
        finally:
            conn.close()

    # ------------------------------------------------------------------ #

    def sync_titles(self, cursor):
        self.stdout.write('  → Titles...')
        existing_ids = set(Title.objects.values_list('id', flat=True))

        cursor.execute("SELECT * FROM titles")
        rows = cursor.fetchall()

        new_rows = [r for r in rows if r['id'] not in existing_ids]
        existing_rows = [r for r in rows if r['id'] in existing_ids]

        # --- Novos títulos ---
        created = 0
        for r in new_rows:
            self.stdout.write(f"     [NOVO] #{r['id']} {r['name']}")
            if not self.dry_run:
                Title.objects.create(
                    id=r['id'],
                    name=r['name'],
                    type_id=r['type_id'],
                    publisher_id=r['publisher_id'],
                    periodicity_id=r['periodicity_id'],
                    format_id=r['size_id'],
                    genre_id=r['genre_id'],
                    subgenre_id=r['subgenre_id'],
                    created_at=r['created_at'] or NOW,
                    updated_at=r['updated_at'] or NOW,
                )
            created += 1

        # --- Títulos potencialmente alterados (updated_at diferente) ---
        updated = 0
        current_map = {
            t.id: t.updated_at
            for t in Title.objects.filter(id__in=[r['id'] for r in existing_rows])
        }
        for r in existing_rows:
            local_updated_at = to_utc_naive(current_map.get(r['id']))
            if r['updated_at'] and local_updated_at and r['updated_at'] != local_updated_at:
                self.stdout.write(f"     [ATUALIZA] #{r['id']} {r['name']}")
                if not self.dry_run:
                    Title.objects.filter(id=r['id']).update(
                        name=r['name'],
                        type_id=r['type_id'],
                        publisher_id=r['publisher_id'],
                        periodicity_id=r['periodicity_id'],
                        format_id=r['size_id'],
                        genre_id=r['genre_id'],
                        subgenre_id=r['subgenre_id'],
                        updated_at=r['updated_at'],
                    )
                updated += 1

        self.stdout.write(f'     {created} novos, {updated} atualizados')

    def sync_issues(self, cursor):
        self.stdout.write('  → Issues...')
        existing_ids = set(Issue.objects.values_list('id', flat=True))

        cursor.execute("SELECT * FROM issues")
        rows = cursor.fetchall()

        new_rows = [r for r in rows if r['id'] not in existing_ids]
        existing_rows = [r for r in rows if r['id'] in existing_ids]

        # --- Issues novas ---
        created = 0
        for r in new_rows:
            self.stdout.write(f"     [NOVO] #{r['id']} {r['name']} #{r['issue_number']}")
            if not self.dry_run:
                Issue.objects.create(
                    id=r['id'],
                    title_id=r['title_id'],
                    name=r['name'],
                    subtitle=r['subtitle'],
                    issue_number=r['issue_number'],
                    date_publication=r['date_publication'],
                    number_pages=r['number_pages'],
                    isbn=r['isbn'],
                    synopsis=r['synopsis'],
                    image=r['image'],
                    created_at=r['created_at'] or NOW,
                    updated_at=r['updated_at'] or NOW,
                )
            created += 1

        # --- Issues alteradas ---
        updated = 0
        current_map = {
            i.id: i.updated_at
            for i in Issue.objects.filter(id__in=[r['id'] for r in existing_rows])
        }
        for r in existing_rows:
            local_updated_at = to_utc_naive(current_map.get(r['id']))
            if r['updated_at'] and local_updated_at and r['updated_at'] != local_updated_at:
                self.stdout.write(f"     [ATUALIZA] #{r['id']} {r['name']}")
                if not self.dry_run:
                    Issue.objects.filter(id=r['id']).update(
                        title_id=r['title_id'],
                        name=r['name'],
                        subtitle=r['subtitle'],
                        issue_number=r['issue_number'],
                        date_publication=r['date_publication'],
                        number_pages=r['number_pages'],
                        isbn=r['isbn'],
                        synopsis=r['synopsis'],
                        image=r['image'],
                        updated_at=r['updated_at'],
                    )
                updated += 1

        self.stdout.write(f'     {created} novas, {updated} atualizadas')

    def sync_collection(self, cursor):
        self.stdout.write('  → CollectionItems...')
        existing_ids = set(CollectionItem.objects.values_list('id', flat=True))
        user = User.objects.first()

        cursor.execute("SELECT * FROM collection")
        rows = cursor.fetchall()

        new_rows = [r for r in rows if r['id'] not in existing_ids]

        created = 0
        skipped = 0
        for r in new_rows:
            # collection não existe mais como coluna única no schema novo
            # (virou has_physical/has_digital). Assume física por padrão,
            # como fizemos na migração original — ajuste se necessário.
            if not Issue.objects.filter(id=r['issue_id']).exists():
                self.stdout.write(self.style.WARNING(
                    f"     [PULADO] collection #{r['id']} referencia issue_id={r['issue_id']} inexistente"
                ))
                skipped += 1
                continue

            self.stdout.write(f"     [NOVO] #{r['id']} issue_id={r['issue_id']}")
            if not self.dry_run:
                CollectionItem.objects.get_or_create(
                    issue_id=r['issue_id'],
                    user=user,
                    defaults=dict(
                        id=r['id'],
                        added_date=r['added_date'],
                        has_physical=True,
                        has_digital=False,
                        created_at=r['created_at'] or NOW,
                        updated_at=r['updated_at'] or NOW,
                    ),
                )
            created += 1

        self.stdout.write(f'     {created} novos, {skipped} pulados (issue inexistente)')
