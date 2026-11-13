"""Настройка раздела «Участники» в административной панели Django."""

from django.contrib import admin

from participants_app.models import Participant
from registrations_app.models import Registration


class ParticipantRegistrationInline(admin.TabularInline):
    """Регистрации участника на странице самого участника."""

    model = Registration
    # Участник не выводится: он и так известен на этой странице.
    fields = ("seminar", "status")
    extra = 0
    # Регистрации здесь не удаляются: история сохраняется.
    can_delete = False
    autocomplete_fields = ("seminar",)


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    """Участники в административной панели."""

    list_display = ("id", "name", "email")
    # Имя — ссылка на страницу редактирования.
    list_display_links = ("name",)
    search_fields = ("name", "email")
    ordering = ("name",)
    list_per_page = 20
    readonly_fields = ("id",)
    # Связанные регистрации в карточке участника.
    inlines = (ParticipantRegistrationInline,)
