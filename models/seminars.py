"""Класс Seminar и функции работы с коллекцией семинаров."""
from datetime import date
from typing import List, Optional


class Seminar:
    """Семинар, доступный для регистрации участников."""

    def __init__(
        self,
        seminar_id: int,
        title: str,
        seminar_date: date,
        max_participants: int,
    ) -> None:
        """Создать объект семинара."""
        self.id = seminar_id
        self.title = title
        self.date = seminar_date
        self.max_participants = max_participants

    def is_available_for(self, registered_count: int) -> bool:
        """Проверить, есть ли свободные места при данном числе регистраций."""
        return registered_count < self.max_participants

    def __str__(self) -> str:
        """Вернуть строковое представление семинара."""
        return f"{self.title} — {self.date} (мест: {self.max_participants})"


def add_seminar(
    seminars: List[Seminar],
    title: str,
    seminar_date: date,
    max_participants: int,
) -> Seminar:
    """Создать семинар и добавить его в коллекцию."""
    seminar_id = max((seminar.id for seminar in seminars), default=0) + 1
    seminar = Seminar(seminar_id, title, seminar_date, max_participants)
    seminars.append(seminar)
    return seminar


def find_seminar(seminars: List[Seminar], query: str) -> List[Seminar]:
    """Найти семинары, в названии которых встречается query."""
    query_lower = query.lower()
    return [
        seminar for seminar in seminars
        if query_lower in seminar.title.lower()
    ]


def find_seminar_by_id(
    seminars: List[Seminar], seminar_id: int
) -> Optional[Seminar]:
    """Найти семинар по идентификатору."""
    for seminar in seminars:
        if seminar.id == seminar_id:
            return seminar
    return None


def sort_seminars(seminars: List[Seminar]) -> List[Seminar]:
    """Вернуть семинары, отсортированные по дате проведения."""
    return sorted(seminars, key=lambda seminar: seminar.date)


def show_seminars(seminars: List[Seminar]) -> None:
    """Вывести список семинаров."""
    if not seminars:
        print("Семинаров пока нет")
        return
    for seminar in sort_seminars(seminars):
        print(f"{seminar.id}. {seminar}")
