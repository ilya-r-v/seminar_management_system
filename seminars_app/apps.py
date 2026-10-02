"""Конфигурация Django-приложения «Семинары»."""
from django.apps import AppConfig


class SeminarsAppConfig(AppConfig):
    """Настройки приложения, регистрируемого в INSTALLED_APPS."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "seminars_app"
