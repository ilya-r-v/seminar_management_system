"""Класс Registration и функции работы с коллекцией регистраций."""
from typing import List, Optional

from .participants import Participant
from .seminars import Seminar


class Registration:
    """Регистрация участника на семинар."""

    def __init__(
        self,
        registration_id: int,
        seminar: Seminar,
        participant: Participant,
    ) -> None:
        """Создать объект регистрации."""
        self.id = registration_id
        self.seminar = seminar
        self.participant = participant
        self.is_cancelled = False

    def cancel(self) -> None:
        """Отменить регистрацию."""
        self.is_cancelled = True

    def __str__(self) -> str:
        """Вернуть строковое представление регистрации."""
        status = "отменена" if self.is_cancelled else "активна"
        return f"{self.participant.name} → {self.seminar.title} ({status})"


def is_registration_open(
    registrations: List[Registration], seminar: Seminar
) -> bool:
    """Проверить, есть ли свободные места на семинаре."""
    registered_count = sum(
        1 for reg in registrations
        if reg.seminar.id == seminar.id and not reg.is_cancelled
    )
    return seminar.is_available_for(registered_count)


def create_registration(
    registrations: List[Registration],
    seminar: Seminar,
    participant: Participant,
) -> Optional[Registration]:
    """Зарегистрировать участника на семинар.

    Повторная активная регистрация одного участника на один семинар
    запрещена. Отменённая регистрация не блокирует повторную запись.
    Если свободных мест нет, регистрация не создаётся.
    """
    for reg in registrations:
        if (
            reg.seminar.id == seminar.id
            and reg.participant.id == participant.id
            and not reg.is_cancelled
        ):
            raise ValueError("Участник уже зарегистрирован на этот семинар")

    if not is_registration_open(registrations, seminar):
        return None

    registration_id = max((reg.id for reg in registrations), default=0) + 1
    registration = Registration(registration_id, seminar, participant)
    registrations.append(registration)
    return registration


def cancel_registration(
    registrations: List[Registration], registration_id: int
) -> bool:
    """Отменить регистрацию по идентификатору."""
    for reg in registrations:
        if reg.id == registration_id:
            reg.cancel()
            return True
    return False


def get_registration_status(current: int, max_count: int) -> str:
    """Вернуть текстовый статус регистрации (функция из ПР1)."""
    free_places = max_count - current
    if free_places > 0:
        return f"Регистрация открыта, свободных мест: {free_places}"
    return "Мест нет, регистрация закрыта"


def show_registrations(registrations: List[Registration]) -> None:
    """Вывести список регистраций."""
    if not registrations:
        print("Регистраций пока нет")
        return
    for reg in registrations:
        print(f"{reg.id}. {reg}")
