"""Функции сохранения и загрузки данных проекта в формате JSON."""
import json
from datetime import date
from typing import List

from models import Participant, Registration, Seminar, Talk
from models.participants import find_participant_by_id
from models.seminars import find_seminar_by_id


def load_seminars(filename: str) -> List[Seminar]:
    """Загрузить семинары из JSON-файла и создать объекты Seminar."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(
            f"Файл {filename} повреждён, начинаем с пустого списка семинаров"
        )
        return []

    return [
        Seminar(
            item["id"],
            item["title"],
            date.fromisoformat(item["date"]),
            item["max_participants"],
        )
        for item in raw_data
    ]


def save_seminars(filename: str, seminars: List[Seminar]) -> None:
    """Сохранить объекты Seminar в JSON-файл."""
    raw_data = [
        {
            "id": seminar.id,
            "title": seminar.title,
            "date": seminar.date.isoformat(),
            "max_participants": seminar.max_participants,
        }
        for seminar in seminars
    ]
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(raw_data, file, ensure_ascii=False, indent=2)


def load_participants(filename: str) -> List[Participant]:
    """Загрузить участников из JSON-файла и создать объекты Participant."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(
            f"Файл {filename} повреждён, "
            "начинаем с пустого списка участников"
        )
        return []

    return [Participant.from_data(item) for item in raw_data]


def save_participants(
    filename: str, participants: List[Participant]
) -> None:
    """Сохранить объекты Participant в JSON-файл."""
    raw_data = [
        {
            "id": participant.id,
            "name": participant.name,
            "email": participant.email,
        }
        for participant in participants
    ]
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(raw_data, file, ensure_ascii=False, indent=2)


def load_registrations(
    filename: str,
    seminars: List[Seminar],
    participants: List[Participant],
) -> List[Registration]:
    """Загрузить регистрации из JSON-файла, связав их с объектами."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(
            f"Файл {filename} повреждён, "
            "начинаем с пустого списка регистраций"
        )
        return []

    registrations = []
    for item in raw_data:
        seminar = find_seminar_by_id(seminars, item["seminar_id"])
        participant = find_participant_by_id(
            participants, item["participant_id"]
        )
        if seminar is None or participant is None:
            continue
        registration = Registration(item["id"], seminar, participant)
        registration.is_cancelled = item["is_cancelled"]
        registrations.append(registration)
    return registrations


def save_registrations(
    filename: str, registrations: List[Registration]
) -> None:
    """Сохранить объекты Registration в JSON-файл."""
    raw_data = [
        {
            "id": reg.id,
            "seminar_id": reg.seminar.id,
            "participant_id": reg.participant.id,
            "is_cancelled": reg.is_cancelled,
        }
        for reg in registrations
    ]
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(raw_data, file, ensure_ascii=False, indent=2)


def load_talks(filename: str, seminars: List[Seminar]) -> List[Talk]:
    """Загрузить доклады из JSON-файла, связав их с объектами Seminar."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(
            f"Файл {filename} повреждён, начинаем с пустого списка докладов"
        )
        return []

    talks = []
    for item in raw_data:
        seminar = find_seminar_by_id(seminars, item["seminar_id"])
        if seminar is None:
            continue
        talks.append(
            Talk(
                item["id"],
                seminar,
                item["title"],
                item["speaker"],
                item["start_time"],
                item["duration_minutes"],
            )
        )
    return talks


def save_talks(filename: str, talks: List[Talk]) -> None:
    """Сохранить объекты Talk в JSON-файл."""
    raw_data = [
        {
            "id": talk.id,
            "seminar_id": talk.seminar.id,
            "title": talk.title,
            "speaker": talk.speaker,
            "start_time": talk.start_time,
            "duration_minutes": talk.duration_minutes,
        }
        for talk in talks
    ]
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(raw_data, file, ensure_ascii=False, indent=2)
