"""Настройка раздела «Регистрации» в административной панели Django."""

from django.contrib import admin, messages

from registrations_app.models import Registration


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    """Регистрации в административной панели."""

    # Столбцы списка. seminar_date и seminar_places — методы ниже,
    # они показывают поля связанного семинара.
    list_display = (
        "id",
        "participant",
        "seminar",
        "seminar_date",
        "seminar_places",
        "status",
    )
    # По нажатию на номер открывается карточка регистрации.
    list_display_links = ("id",)
    # Поиск по полям связанных моделей (через двойное подчёркивание).
    search_fields = (
        "participant__name",
        "participant__email",
        "seminar__title",
    )
    # Фильтры справа от списка.
    list_filter = ("status", "seminar__seminar_date", "seminar")
    # Сначала регистрации на более поздние семинары.
    ordering = ("-seminar__seminar_date", "id")
    list_per_page = 20
    # Номер можно видеть, но нельзя менять.
    readonly_fields = ("id",)
    # Семинар и участник загружаются тем же запросом, что и список:
    # без этого на каждую строку шло бы по два лишних запроса.
    list_select_related = ("seminar", "participant")
    # Быстрая навигация по датам семинаров над списком.
    date_hierarchy = "seminar__seminar_date"
    # Выбор семинара и участника с поиском по мере ввода.
    autocomplete_fields = ("seminar", "participant")
    # Массовые действия в меню над списком.
    actions = ("cancel_registrations", "restore_registrations")

    @admin.display(
        description="Дата семинара",
        ordering="seminar__seminar_date",
    )
    def seminar_date(self, obj):
        """Дата связанного семинара."""
        return obj.seminar.seminar_date

    @admin.display(
        description="Мест на семинаре",
        ordering="seminar__max_participants",
    )
    def seminar_places(self, obj):
        """Максимальное число участников связанного семинара."""
        return obj.seminar.max_participants

    @admin.action(description="Отменить выбранные регистрации")
    def cancel_registrations(self, request, queryset):
        """Отменить отмеченные регистрации методом модели cancel()."""
        count = 0
        for registration in queryset:
            registration.cancel()
            count += 1
        self.message_user(
            request,
            f"Отменено регистраций: {count}.",
            messages.SUCCESS,
        )

    @admin.action(description="Вернуть в активные")
    def restore_registrations(self, request, queryset):
        """Сделать отмеченные регистрации снова активными."""
        # Простое изменение одного поля: достаточно одного запроса.
        updated = queryset.update(status=Registration.Status.ACTIVE)
        self.message_user(
            request,
            f"Возвращено регистраций: {updated}.",
            messages.SUCCESS,
        )
