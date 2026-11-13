"""Конфигурация Django-приложения «Главная страница»."""
from django.apps import AppConfig


class HomepageConfig(AppConfig):
    """Настройки приложения, регистрируемого в INSTALLED_APPS."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "homepage"
    # Название раздела в административной панели.
    verbose_name = "Главная страница"
