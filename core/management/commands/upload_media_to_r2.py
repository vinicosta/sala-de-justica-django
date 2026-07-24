"""
core/management/commands/upload_media_to_r2.py

Sobe todos os arquivos de MEDIA_ROOT (capas já sincronizadas localmente)
para o bucket Cloudflare R2, preservando os paths relativos — essencial
porque o campo `image` do model Issue guarda só o path relativo, que
precisa bater exatamente com a key do objeto no bucket.

Uso:
    docker compose exec web python manage.py upload_media_to_r2 --dry-run
    docker compose exec web python manage.py upload_media_to_r2
"""

import os

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Sobe os arquivos de MEDIA_ROOT local para o bucket Cloudflare R2'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas lista o que seria enviado, sem subir nada',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        access_key = os.environ.get('R2_ACCESS_KEY_ID')
        secret_key = os.environ.get('R2_SECRET_ACCESS_KEY')
        bucket = os.environ.get('R2_BUCKET_NAME', 'slj-covers')
        endpoint = os.environ.get('R2_ENDPOINT_URL')
        verify_ssl = os.environ.get('R2_VERIFY_SSL', 'True') != 'False'

        if not all([access_key, secret_key, endpoint]):
            self.stderr.write(self.style.ERROR(
                'Defina R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY e R2_ENDPOINT_URL antes de rodar.'
            ))
            return

        if not verify_ssl:
            self.stdout.write(self.style.WARNING(
                '⚠️  Verificação SSL desabilitada (R2_VERIFY_SSL=False) — use só em rede confiável'
            ))

        s3 = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='auto',
            verify=verify_ssl,
        )

        media_root = settings.MEDIA_ROOT
        total = 0
        uploaded = 0
        skipped = 0

        for root, _dirs, files in os.walk(media_root):
            for filename in files:
                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, media_root).replace(os.sep, '/')
                total += 1

                if dry_run:
                    self.stdout.write(f'  [SUBIRIA] {relative_path}')
                    continue

                try:
                    s3.upload_file(full_path, bucket, relative_path)
                    uploaded += 1
                    if uploaded % 200 == 0:
                        self.stdout.write(f'  ... {uploaded}/{total} enviados')
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'  [ERRO] {relative_path}: {e}'))
                    skipped += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(f'🔍 Dry-run: {total} arquivos seriam enviados'))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'✅ {uploaded}/{total} arquivos enviados ({skipped} com erro)'
            ))
