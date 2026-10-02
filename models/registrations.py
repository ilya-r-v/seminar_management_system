"""Класс и функции для работы с регистрациями участников на семинары."""

from typing import List, Optional

from models.participants import Participant
from models.seminars import Seminar


class Registration:
    """Регистрация участника на семинар."""

    def __init__(
        self,
        registration_id: int,
        seminar: Seminar,
        participant: Participant,
        is_cancelled: bool = False,
    ) -> None:
        self.id = registration_id
        self.seminar = seminar
        self.participant = participant
        self.is_cancelled = is_cancelled

    def cancel(self) -> None:
        """Отменить регистрацию."""
        self.is_cancelled = True

    def __str__(self) -> str:
        status = "отменена" if self.is_cancelled else "активна"
        return (
            f"{self.participant.name} -> {self.seminar.title} " f"({status})"
        )


def is_registration_open(
    registrations: List[Registration], seminar: Seminar
) -> bool:
    """Проверить, есть ли свободные места на семинаре."""
    registered_count = sum(
        1
        for reg in registrations
        if reg.seminar.id == seminar.id and not reg.is_cancelled
    )
    return seminar.is_available_for(registered_count)


def create_registration(
    registrations: List[Registration],
    seminar: Seminar,
    participant: Participant,
) -> Optional[Registration]:
    """Зарегистрировать участника на семинар.

    Повторная активная регистрация того же участника на тот же
    семинар запрещена. Если свободных мест нет, возвращает None.
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

    new_id = max((r.id for r in registrations), default=0) + 1
    registration = Registration(new_id, seminar, participant)
    registrations.append(registration)
    return registration


def cancel_registration(
    registrations: List[Registration], registration_id: int
) -> bool:
    """Отменить регистрацию по идентификатору."""
    for reg in registrations:
        if reg.id == registration_id and not reg.is_cancelled:
            reg.cancel()
            return True
    return False


def find_registration_by_id(
    registrations: List[Registration], registration_id: int
) -> Optional[Registration]:
    """Найти регистрацию по идентификатору."""
    for reg in registrations:
        if reg.id == registration_id:
            return reg
    return None


def get_registration_status(current: int, max_count: int) -> str:
    """Вернуть текстовый статус регистрации (функция из ПР1)."""
    if current >= max_count:
        return "Мест нет"
    return f"Свободно мест: {max_count - current}"


def show_registrations(registrations: List[Registration]) -> None:
    """Вывести список регистраций в консоль."""
    if not registrations:
        print("Регистраций пока нет")
        return
    for reg in registrations:
        print(f"{reg.id}. {reg}")
