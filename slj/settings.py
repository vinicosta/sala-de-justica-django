from pathlib import Path
import os
from dotenv import load_dotenv
from django.templatetags.static import static

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost 127.0.0.1').split()

# Diz ao Django para confiar no header que o proxy do Railway usa
# pra indicar que a requisição original era HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Origens confiáveis para verificação de CSRF em produção
CSRF_TRUSTED_ORIGINS = [
    "https://app.saladejustica.com.br",
    "https://sala-de-justica-django-production.up.railway.app",
]

LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/admin/"

INSTALLED_APPS = [
    # Unfold DEVE vir antes de django.contrib.admin
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # Apps locais
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "slj.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.gravatar",
            ],
        },
    },
]

WSGI_APPLICATION = "slj.wsgi.application"

# --- Banco de dados PostgreSQL ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATABASE_NAME", "slj_app"),
        "USER": os.environ.get("DATABASE_USER", "slj_user"),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", ""),
        "HOST": os.environ.get("DATABASE_HOST", "db"),
        "PORT": os.environ.get("DATABASE_PORT", "5432"),
    }
}

# --- Internacionalização ---
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# --- Static & Media ---
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

USE_R2 = os.environ.get("USE_R2", "False") == "True"

if USE_R2:
    # --- Cloudflare R2 (produção) ---
    AWS_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME", "slj-covers")
    AWS_S3_ENDPOINT_URL = os.environ.get("R2_ENDPOINT_URL")
    AWS_S3_REGION_NAME = "auto"
    AWS_S3_ADDRESSING_STYLE = "virtual"
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False       # URLs públicas, sem assinatura/expiração
    AWS_S3_FILE_OVERWRITE = False

    R2_PUBLIC_DOMAIN = os.environ.get("R2_PUBLIC_DOMAIN")  # ex: pub-xxxx.r2.dev
    MEDIA_URL = f"https://{R2_PUBLIC_DOMAIN}/"

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
else:
    # --- Disco local (desenvolvimento, Docker) ---
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"

    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Unfold Admin ---
UNFOLD = {
    "SITE_TITLE": "Sala de Justiça / App",
    "SITE_HEADER": "Sala de Justiça / App",
    "SITE_SYMBOL": "menu_book",
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/x-icon",
            "href": lambda request: static("core/favicon.ico"),
        },
    ],
    "SITE_ICON": lambda request: static("core/favicon.png"),
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "THEME": None,
    "SHOW_THEME_SWITCHER": True,
    "DASHBOARD_CALLBACK": "core.dashboard.dashboard_callback",
    "COLORS": {
        "primary": {
            "50":  "239 246 255",
            "100": "219 234 254",
            "200": "191 219 254",
            "300": "147 197 253",
            "400": "96 165 250",
            "500": "55 138 221",
            "600": "37 99 185",
            "700": "29 78 157",
            "800": "30 64 130",
            "900": "23 48 107",
            "950": "15 30 75",
        },
    },
    "SIDEBAR": {
        "show_search": False,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Acervo",
                "separator": False,
                "items": [
                    {
                        "title": "Quadrinhos",
                        "icon": "comic_bubble",
                        "link": "/quadrinhos/",
                    },
                    {
                        "title": "Livros",
                        "icon": "menu_book",
                        "link": "/livros/",
                    },
                    {
                        "title": "Revistas",
                        "icon": "newspaper",
                        "link": "/revistas/",
                    },
                ],
            },
            {
                "title": "Cadastros",
                "separator": True,
                "items": [
                    {
                        "title": "Autores",
                        "icon": "person",
                        "link": "/autores/",
                    },
                    {
                        "title": "Editoras",
                        "icon": "business",
                        "link": "/editoras/",
                    },
                    {
                        "title": "Formatos",
                        "icon": "style",
                        "link": "/formatos/",
                    },
                    {
                        "title": "Gêneros",
                        "icon": "category",
                        "link": "/generos/",
                    },
                    {
                        "title": "Subgêneros",
                        "icon": "sell",
                        "link": "/subgeneros/",
                    },
                    {
                        "title": "Periodicidades",
                        "icon": "event_repeat",
                        "link": "/periodicidades/",
                    },
                ],
            },
            {
                "title": "Sistema",
                "separator": True,
                "items": [
                    {
                        "title": "Usuários",
                        "icon": "manage_accounts",
                        "link": "/admin/auth/user/",
                    },
                ],
            },
        ],
    },
}
