"""Модели приложения «Участники» (Django ORM)."""

from django.db import models


class Participant(models.Model):
    """Участник семинаров.

    Это участник предметной области, а не встроенный пользователь
    Django: входа в систему и паролей у него нет.
    """

    # Имя участника.
    name = models.CharField(
        max_length=200,
        verbose_name="Имя участника",
    )

    # Электронная почта участника.
    email = models.EmailField(
        verbose_name="Электронная почта",
    )

    class Meta:
        # Сортировка по умолчанию: по имени.
        ordering = ["name"]
        verbose_name = "Участник"
        verbose_name_plural = "Участники"

    def __str__(self):
        # Текстовое представление в админке и Django shell.
        return self.name
