"""Настройка раздела «Семинары» в административной панели Django."""

from django.contrib import admin
from django.db.models import Count, Q
from django.utils.html import format_html

from registrations_app.models import Registration
from seminars_app.models import Seminar, Talk


class TalkInline(admin.TabularInline):
    """Доклады семинара на странице самого семинара."""

    model = Talk
    fields = ("title", "speaker", "start_time", "duration_minutes")
    # Пустые строки для новых докладов заранее не показываются.
    extra = 0


class SeminarRegistrationInline(admin.TabularInline):
    """Регистрации на семинар на странице самого семинара."""

    model = Registration
    # Семинар не выводится: он и так известен на этой странице.
    fields = ("participant", "status")
    extra = 0
    # Регистрации здесь не удаляются: история сохраняется.
    can_delete = False
    autocomplete_fields = ("participant",)


@admin.register(Seminar)
class SeminarAdmin(admin.ModelAdmin):
    """Семинары в административной панели."""

    # Столбцы списка. active_registrations и site_link — методы ниже.
    list_display = (
        "id",
        "title",
        "seminar_date",
        "max_participants",
        "active_registrations",
        "is_large",
        "site_link",
    )
    # Название — ссылка на страницу редактирования.
    list_display_links = ("title",)
    # Число мест можно менять прямо в списке.
    list_editable = ("max_participants",)
    search_fields = ("title",)
    list_filter = ("seminar_date", "is_large")
    ordering = ("seminar_date", "title")
    list_per_page = 20
    # Эти поля показываются в форме, но менять их нельзя:
    # id и slug назначаются автоматически, is_large считает база.
    readonly_fields = ("id", "slug", "is_large")
    date_hierarchy = "seminar_date"
    # Связанные доклады и регистрации в карточке семинара.
    inlines = (TalkInline, SeminarRegistrationInline)
    # Ссылка «Смотреть на сайте» (использует get_absolute_url()).
    view_on_site = True

    def get_queryset(self, request):
        """Добавить к семинарам число активных регистраций."""
        # Значение считается одним запросом для всего списка,
        # а не отдельным запросом на каждую строку.
        queryset = super().get_queryset(request)
        return queryset.annotate(
            active_registrations_count=Count(
                "registrations",
                filter=Q(
                    registrations__status=Registration.Status.ACTIVE
                ),
            ),
        )

    @admin.display(
        description="Активных регистраций",
        ordering="active_registrations_count",
    )
    def active_registrations(self, obj):
        """Готовое значение из аннотации в get_queryset()."""
        return obj.active_registrations_count

    @admin.display(description="Страница на сайте")
    def site_link(self, obj):
        """Ссылка на страницу семинара на сайте."""
        return format_html(
            '<a href="{}" target="_blank">Открыть</a>',
            obj.get_absolute_url(),
        )


@admin.register(Talk)
class TalkAdmin(admin.ModelAdmin):
    """Доклады в административной панели."""

    list_display = ("id", "title", "speaker", "seminar", "start_time")
    list_display_links = ("title",)
    search_fields = ("title", "speaker", "seminar__title")
    list_filter = ("seminar",)
    ordering = ("seminar__seminar_date", "start_time")
    list_per_page = 20
    readonly_fields = ("id",)
    list_select_related = ("seminar",)
    autocomplete_fields = ("seminar",)
