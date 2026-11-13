"""Модели приложения «Регистрации» (Django ORM)."""

from django.db import models

# Модели, с которыми связана регистрация.
from participants_app.models import Participant
from seminars_app.models import Seminar


class RegistrationQuerySet(models.QuerySet):
    """Набор запросов для работы с регистрациями."""

    def active(self):
        """Только активные регистрации."""
        return self.filter(status=self.model.Status.ACTIVE)

    def cancelled(self):
        """Только отменённые регистрации."""
        return self.filter(status=self.model.Status.CANCELLED)

    def completed(self):
        """Только завершённые регистрации."""
        return self.filter(status=self.model.Status.COMPLETED)

    def for_date(self, selected_date):
        """Регистрации на семинары, которые проходят в указанную дату."""
        return self.filter(seminar__seminar_date=selected_date)


class RegistrationManager(
    models.Manager.from_queryset(RegistrationQuerySet)
):
    """Менеджер модели Registration с дополнительными методами.

    Registration.objects.all() по-прежнему возвращает все записи,
    фильтрация происходит только при явном вызове active() и других.
    """


class Registration(models.Model):
    """Регистрация участника на семинар."""

    class Status(models.TextChoices):
        """Состояния регистрации: код в базе и название для человека."""

        # Регистрация действует и занимает место на семинаре.
        ACTIVE = "active", "Активна"
        # Регистрация отменена, место освобождено.
        CANCELLED = "cancelled", "Отменена"
        # Семинар прошёл, регистрация закрыта.
        COMPLETED = "completed", "Завершена"

    # Семинар, на который оформлена регистрация.
    # PROTECT запрещает удалить семинар, пока на него есть регистрации:
    # так сохраняется история регистраций.
    seminar = models.ForeignKey(
        Seminar,
        on_delete=models.PROTECT,
        related_name="registrations",
        verbose_name="Семинар",
    )

    # Участник, оформивший регистрацию.
    participant = models.ForeignKey(
        Participant,
        on_delete=models.PROTECT,
        related_name="registrations",
        verbose_name="Участник",
    )

    # Статус регистрации. Новая регистрация по умолчанию активна.
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Статус регистрации",
    )

    # Менеджер с методами active(), cancelled(), completed(), for_date().
    objects = RegistrationManager()

    class Meta:
        # Сортировка по умолчанию: по дате семинара, затем по id.
        ordering = ["seminar__seminar_date", "pk"]
        verbose_name = "Регистрация"
        verbose_name_plural = "Регистрации"

    def __str__(self):
        return f"{self.participant} — {self.seminar}"

    def cancel(self):
        """Отменить регистрацию и сохранить изменение в базе."""
        self.status = self.Status.CANCELLED
        # Обновляем в базе только изменённое поле.
        self.save(update_fields=["status"])
