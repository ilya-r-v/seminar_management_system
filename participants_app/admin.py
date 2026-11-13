"""Регистрация моделей приложения в административной панели Django."""

from django.contrib import admin

from participants_app.models import Participant


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    """Участники в административной панели."""

    list_display = ("id", "name", "email")
    search_fields = ("name", "email")
