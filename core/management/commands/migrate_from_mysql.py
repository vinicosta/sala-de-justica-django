"""
core/management/commands/migrate_from_mysql.py

Migra dados do MySQL legado para o PostgreSQL Django.

v2: aceita --source-db para permitir apontar tanto para `salade10_app`
(snapshot original) quanto para `salade10_app_new` (dump mais recente
do Hostgator), útil para re-executar a migração completa do zero.

Uso:
    docker compose exec web python manage.py migrate_from_mysql
    docker compose exec web python manage.py migrate_from_mysql --source-db=salade10_app_new
"""

import pymysql
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import (
    Type, Publisher, Genre, Subgenre, Periodicity,
    Format, Author, Title, Issue, CollectionItem, ReadItem, ReadingList
)

NOW = timezone.now()


class Command(BaseCommand):
    help = 'Migra dados do MySQL legado para o PostgreSQL Django'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source-db',
            default='salade10_app',
            help='Nome da base MySQL de origem (default: salade10_app)',
        )

    def handle(self, *args, **kwargs):
        mysql_config = {
            'host': 'mysql_legacy',
            'port': 3306,
            'user': 'root',
            'password': 'legacy_root',
            'database': kwargs['source_db'],
            'charset': 'utf8mb4',
            'use_unicode': True,
            'cursorclass': pymysql.cursors.DictCursor,
        }

        self.stdout.write(f"📦 Fonte: {kwargs['source_db']}")
        conn = pymysql.connect(**mysql_config)

        try:
            # Força charset UTF-8 na sessão
            with conn.cursor() as c:
                c.execute("SET NAMES utf8mb4")
                c.execute("SET CHARACTER SET utf8mb4")
                c.execute("SET character_set_connection=utf8mb4")
                c.execute("SET time_zone = '+00:00'")

            self.stdout.write('🔌 Conectado ao MySQL legado')

            with conn.cursor() as cursor:
                self.migrate_publishers(cursor)
                self.migrate_genres(cursor)
                self.migrate_subgenres(cursor)
                self.migrate_periodicities(cursor)
                self.migrate_formats(cursor)
                self.migrate_authors(cursor)
                self.migrate_titles(cursor)
                self.migrate_issues(cursor)
                self.migrate_author_issues(cursor)
                self.migrate_collection(cursor)
                self.migrate_readed(cursor)
                self.migrate_reading(cursor)
            self.stdout.write(self.style.SUCCESS('✅ Migração concluída com sucesso!'))
        finally:
            conn.close()

    # ------------------------------------------------------------------ #

    def migrate_publishers(self, cursor):
        self.stdout.write('  → Publishers...')
        cursor.execute("SELECT * FROM publishers")
        rows = cursor.fetchall()
        objs = [
            Publisher(
                id=r['id'],
                name=r['name'],
                created_at=r['created_at'] or NOW,
                updated_at=r['updated_at'] or NOW,
            )
            for r in rows
        ]
        Publisher.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'     {len(objs)} publishers migrados')

    def migrate_genres(self, cursor):
        self.stdout.write('  → Genres...')
        cursor.execute("SELECT * FROM genres")
        rows = cursor.fetchall()
        objs = [
            Genre(
                id=r['id'],
                name=r['name'],
                created_at=r['created_at'] or NOW,
                updated_at=r['updated_at'] or NOW,
            )
            for r in rows
        ]
        Genre.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'     {len(objs)} genres migrados')

    def migrate_subgenres(self, cursor):
        self.stdout.write('  → Subgenres...')
        cursor.execute("SELECT * FROM subgenres")
        rows = cursor.fetchall()
        objs = [
            Subgenre(
                id=r['id'],
                name=r['name'],
                genre_id=r['genre_id'],
                created_at=r['created_at'] or NOW,
                updated_at=r['updated_at'] or NOW,
            )
            for r in rows
        ]
        Subgenre.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'     {len(objs)} subgenres migrados')

    def migrate_periodicities(self, cursor):
        self.stdout.write('  → Periodicities...')
        cursor.execute("SELECT * FROM periodicities")
        rows = cursor.fetchall()
        objs = [
            Periodicity(
                id=r['id'],
                name=r['name'],
                date_interval=r['date_interval'],
                date_interval_number=r['date_interval_number'],
                created_at=r['created_at'] or NOW,
                updated_at=r['updated_at'] or NOW,
            )
            for r in rows
        ]
        Periodicity.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'     {len(objs)} periodicities migradas')

    def migrate_formats(self, cursor):
        self.stdout.write('  → Formats (sizes)...')
        cursor.execute("SELECT * FROM sizes")
        rows = cursor.fetchall()
        objs = [
            Format(
                id=r['id'],
                name=r['name'],
                type_id=r['type_id'],
                created_at=r['created_at'] or NOW,
                updated_at=r['updated_at'] or NOW,
            )
            for r in rows
        ]
        Format.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'     {len(objs)} formats migrados')

    def migrate_authors(self, cursor):
        self.stdout.write('  → Authors...')
        cursor.execute("SELECT * FROM authors")
        rows = cursor.fetchall()
        objs = [
            Author(
                id=r['id'],
                name=r['name'],
                created_at=r['created_at'] or NOW,
                updated_at=r['updated_at'] or NOW,
            )
            for r in rows
        ]
        Author.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'     {len(objs)} authors migrados')

    def migrate_titles(self, cursor):
        self.stdout.write('  → Titles...')
        cursor.execute("SELECT * FROM titles")
        rows = cursor.fetchall()
        objs = [
            Title(
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
            for r in rows
        ]
        Title.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'     {len(objs)} titles migrados')

    def migrate_issues(self, cursor):
        self.stdout.write('  → Issues...')
        cursor.execute("SELECT * FROM issues")
        rows = cursor.fetchall()
        objs = [
            Issue(
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
            for r in rows
        ]
        Issue.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'     {len(objs)} issues migrados')

    def migrate_author_issues(self, cursor):
        self.stdout.write('  → Author-Issue (M2M)...')
        cursor.execute("SELECT * FROM author_issue")
        rows = cursor.fetchall()
        count = 0
        for r in rows:
            try:
                issue = Issue.objects.get(pk=r['issue_id'])
                issue.authors.add(r['author_id'])
                count += 1
            except Issue.DoesNotExist:
                pass
        self.stdout.write(f'     {count} relações author-issue migradas')

    def migrate_collection(self, cursor):
        self.stdout.write('  → CollectionItems...')
        from django.contrib.auth.models import User
        user = User.objects.first()
        cursor.execute("SELECT * FROM collection")
        rows = cursor.fetchall()
        objs = [
            CollectionItem(
                id=r['id'],
                issue_id=r['issue_id'],
                user=user,
                added_date=r['added_date'],
                created_at=r['created_at'] or NOW,
                updated_at=r['updated_at'] or NOW,
            )
            for r in rows
        ]
        CollectionItem.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'     {len(objs)} collection items migrados')

    def migrate_readed(self, cursor):
        self.stdout.write('  → ReadItems...')
        from django.contrib.auth.models import User
        user = User.objects.first()
        cursor.execute("SELECT * FROM readed")
        rows = cursor.fetchall()
        objs = [
            ReadItem(
                id=r['id'],
                issue_id=r['issue_id'],
                user=user,
                read_date=r['readed_date'],
                created_at=r['created_at'] or NOW,
                updated_at=r['updated_at'] or NOW,
            )
            for r in rows
        ]
        ReadItem.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'     {len(objs)} read items migrados')

    def migrate_reading(self, cursor):
        self.stdout.write('  → ReadingLists...')
        from django.contrib.auth.models import User
        user = User.objects.first()
        cursor.execute("SELECT * FROM reading")
        rows = cursor.fetchall()
        objs = [
            ReadingList(
                id=r['id'],
                title_id=r['title_id'],
                user=user,
                created_at=r['created_at'] or NOW,
                updated_at=r['updated_at'] or NOW,
            )
            for r in rows
        ]
        ReadingList.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'     {len(objs)} reading lists migradas')
