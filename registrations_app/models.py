"""Модели приложения «Регистрации» (Django ORM)."""

from django.db import models

# Модели, с которыми связана регистрация.
from participants_app.models import Participant
from seminars_app.models import Seminar


class Registration(models.Model):
    """Регистрация участника на семинар."""

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

    # Признак отмены. Новая регистрация по умолчанию активна.
    is_cancelled = models.BooleanField(
        default=False,
        verbose_name="Регистрация отменена",
    )

    class Meta:
        # Сортировка по умолчанию: по дате семинара, затем по id.
        ordering = ["seminar__seminar_date", "pk"]
        verbose_name = "Регистрация"
        verbose_name_plural = "Регистрации"

    def __str__(self):
        return f"{self.participant} — {self.seminar}"

    def cancel(self):
        """Отменить регистрацию и сохранить изменение в базе."""
        self.is_cancelled = True
        # Обновляем в базе только изменённое поле.
        self.save(update_fields=["is_cancelled"])
