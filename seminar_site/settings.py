"""
Настройки Django для проекта seminar_site.
"""

import os
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = (
    "django-insecure-v1m&uy-!@04nhregx^on3(&h&v!4ipp1yr+idsi$p9fx@pt6qj"
)

# Режим отладки включён для локальной разработки: он нужен
# для Django Debug Toolbar. Запуск с DJANGO_DEBUG=0 выключает его,
# тогда вместо отладочной страницы видна собственная страница 404.
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

# Признак запуска автотестов: в тестах панель отладки не подключается.
TESTING = "test" in sys.argv

# Панель отладки показывается только для локальных запросов.
INTERNAL_IPS = ["127.0.0.1"]

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "homepage",
    "seminars_app",
    "participants_app",
    "registrations_app",
]

# Django Debug Toolbar: анализ SQL-запросов (только при разработке).
if DEBUG and not TESTING:
    INSTALLED_APPS.append("debug_toolbar")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Панель отладки ставится сразу после SecurityMiddleware.
if DEBUG and not TESTING:
    MIDDLEWARE.insert(
        1, "debug_toolbar.middleware.DebugToolbarMiddleware"
    )

ROOT_URLCONF = "seminar_site.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Общие данные сайта: название и число семинаров.
                "seminars_app.context_processors.seminar_context",
            ],
        },
    },
]

WSGI_APPLICATION = "seminar_site.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]

LANGUAGE_CODE = "ru-RU"

TIME_ZONE = "Europe/Moscow"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
