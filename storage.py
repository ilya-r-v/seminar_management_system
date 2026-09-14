"""Функции сохранения и загрузки данных проекта в формате JSON."""
import json
from datetime import date


def load_seminars(filename: str) -> dict[int, dict]:
    """Загрузить семинары из JSON-файла."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(
            f"Файл {filename} повреждён, начинаем с пустого списка семинаров"
        )
        return {}

    seminars = {}
    for item in raw_data:
        seminars[item["id"]] = {
            "title": item["title"],
            "date": date.fromisoformat(item["date"]),
            "max_participants": item["max_participants"],
        }
    return seminars


def save_seminars(filename: str, seminars: dict[int, dict]) -> None:
    """Сохранить семинары в JSON-файл."""
    raw_data = [
        {
            "id": seminar_id,
            "title": data["title"],
            "date": data["date"].isoformat(),
            "max_participants": data["max_participants"],
        }
        for seminar_id, data in seminars.items()
    ]
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(raw_data, file, ensure_ascii=False, indent=2)


def load_registrations(filename: str) -> list[dict]:
    """Загрузить регистрации участников из JSON-файла."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(
            f"Файл {filename} повреждён, начинаем с пустого списка регистраций"
        )
        return []


def save_registrations(filename: str, registrations: list[dict]) -> None:
    """Сохранить регистрации участников в JSON-файл."""
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(registrations, file, ensure_ascii=False, indent=2)


def load_talks(filename: str) -> list[dict]:
    """Загрузить доклады из JSON-файла."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(
            f"Файл {filename} повреждён, начинаем с пустого списка докладов"
        )
        return []


def save_talks(filename: str, talks: list[dict]) -> None:
    """Сохранить доклады в JSON-файл."""
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(talks, file, ensure_ascii=False, indent=2)