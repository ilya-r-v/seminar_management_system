"""Конфигурация Django-приложения «Участники»."""
from django.apps import AppConfig


class ParticipantsAppConfig(AppConfig):
    """Настройки приложения, регистрируемого в INSTALLED_APPS."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "participants_app"
