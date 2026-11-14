"""Пользовательские валидаторы приложения «Семинары»."""

from django.core.exceptions import ValidationError


def validate_places(value):
    """Проверить, что на семинаре есть хотя бы одно место.

    Валидатор — обычная функция: получает значение поля и вызывает
    ValidationError, если значение не подходит.
    """
    if value < 1:
        raise ValidationError(
            "Число мест должно быть не меньше одного."
        )
