"""Конфигурация Django-приложения «Регистрации»."""
from django.apps import AppConfig


class RegistrationsAppConfig(AppConfig):
    """Настройки приложения, регистрируемого в INSTALLED_APPS."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "registrations_app"
