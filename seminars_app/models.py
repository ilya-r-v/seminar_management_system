"""Модели приложения «Семинары» (Django ORM)."""

from django.db import models
from django.db.models import Count, F, Q


class SeminarQuerySet(models.QuerySet):
    """Дополнительные запросы для семинаров."""

    def with_places(self):
        """Добавить к каждому семинару число занятых и свободных мест.

        Считаются только активные (не отменённые) регистрации.
        Условие стоит внутри Count, а не в filter(), поэтому семинары
        без регистраций остаются в выборке со значением 0
        (аналог LEFT JOIN + GROUP BY из ПР7).
        """
        return self.annotate(
            registered_count=Count(
                "registrations",
                filter=Q(registrations__is_cancelled=False),
            ),
        ).annotate(
            free_places=F("max_participants") - F("registered_count"),
        )


class Seminar(models.Model):
    """Семинар."""

    # Название семинара.
    title = models.CharField(
        max_length=200,
        verbose_name="Название",
    )

    # Дата проведения. DateField хранит дату, а не произвольную строку.
    seminar_date = models.DateField(
        verbose_name="Дата проведения",
    )

    # Максимальное число участников (неотрицательное целое).
    max_participants = models.PositiveIntegerField(
        verbose_name="Максимум участников",
    )

    # Менеджер с дополнительным методом with_places().
    objects = SeminarQuerySet.as_manager()

    class Meta:
        # Сортировка по умолчанию: по дате, затем по идентификатору.
        ordering = ["seminar_date", "pk"]
        verbose_name = "Семинар"
        verbose_name_plural = "Семинары"

    def __str__(self):
        # Текстовое представление в админке и Django shell.
        return self.title


class Talk(models.Model):
    """Доклад в программе семинара."""

    # Семинар, к которому относится доклад.
    # CASCADE: доклад не существует без семинара и удаляется вместе с ним.
    seminar = models.ForeignKey(
        Seminar,
        on_delete=models.CASCADE,
        related_name="talks",
        verbose_name="Семинар",
    )

    # Название доклада.
    title = models.CharField(
        max_length=200,
        verbose_name="Название доклада",
    )

    # Докладчик.
    speaker = models.CharField(
        max_length=200,
        verbose_name="Докладчик",
    )

    # Время начала доклада.
    start_time = models.TimeField(
        verbose_name="Время начала",
    )

    # Длительность доклада в минутах.
    duration_minutes = models.PositiveIntegerField(
        verbose_name="Длительность, мин",
    )

    class Meta:
        # Сортировка по умолчанию: по времени начала.
        ordering = ["start_time", "pk"]
        verbose_name = "Доклад"
        verbose_name_plural = "Доклады"

    def __str__(self):
        return f"{self.title} ({self.speaker})"
