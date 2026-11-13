"""Регистрация моделей приложения в административной панели Django."""

from django.contrib import admin

from registrations_app.models import Registration


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    """Регистрации в административной панели."""

    list_display = ("id", "participant", "seminar", "is_cancelled")
    list_filter = ("is_cancelled", "seminar")
