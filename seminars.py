"""Функции для работы с семинарами."""
from datetime import date


def add_seminar(
    seminars: dict[int, dict],
    title: str,
    seminar_date: date,
    max_participants: int,
) -> int:
    """Добавить семинар в словарь seminars и вернуть его идентификатор."""
    seminar_id = max(seminars.keys(), default=0) + 1
    seminars[seminar_id] = {
        "title": title,
        "date": seminar_date,
        "max_participants": max_participants,
    }
    return seminar_id


def find_seminar(seminars: dict[int, dict], query: str) -> list[int]:
    """Найти идентификаторы семинаров, в названии которых встречается query."""
    query_lower = query.lower()
    found = []
    for seminar_id, data in seminars.items():
        if query_lower in data["title"].lower():
            found.append(seminar_id)
    return found


def check_seminar_capacity(
    seminars: dict[int, dict],
    seminar_id: int,
    registered_count: int,
) -> bool:
    """Проверить, есть ли на семинаре свободные места."""
    seminar = seminars.get(seminar_id)
    if seminar is None:
        raise KeyError(f"Семинар с id={seminar_id} не найден")
    return registered_count < seminar["max_participants"]


def sort_seminars(seminars: dict[int, dict]) -> list[tuple[int, dict]]:
    """Вернуть семинары, отсортированные по дате проведения."""
    return sorted(seminars.items(), key=lambda item: item[1]["date"])
