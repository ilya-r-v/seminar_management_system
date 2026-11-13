"""Регистрация моделей приложения в административной панели Django."""

from django.contrib import admin

from seminars_app.models import Seminar, Talk


@admin.register(Seminar)
class SeminarAdmin(admin.ModelAdmin):
    """Семинары в административной панели."""

    list_display = ("id", "title", "seminar_date", "max_participants")
    search_fields = ("title",)


@admin.register(Talk)
class TalkAdmin(admin.ModelAdmin):
    """Доклады в административной панели."""

    list_display = ("id", "title", "speaker", "seminar", "start_time")
    list_filter = ("seminar",)
