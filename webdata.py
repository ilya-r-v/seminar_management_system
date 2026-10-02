"""Загрузка данных проекта для веб-интерфейса (используется views.py).
"""

from typing import List

from models import Participant, Registration, Seminar, Talk
from storage import (
    load_participants,
    load_registrations,
    load_seminars,
    load_talks,
)

SEMINARS_FILE = "data/seminars.json"
PARTICIPANTS_FILE = "data/participants.json"
REGISTRATIONS_FILE = "data/registrations.json"
TALKS_FILE = "data/talks.json"


def get_seminars() -> List[Seminar]:
    """Загрузить список семинаров из файла."""
    return load_seminars(SEMINARS_FILE)


def get_participants() -> List[Participant]:
    """Загрузить список участников из файла."""
    return load_participants(PARTICIPANTS_FILE)


def get_registrations() -> List[Registration]:
    """Загрузить список регистраций из файла, связав с объектами."""
    seminars = get_seminars()
    participants = get_participants()
    return load_registrations(REGISTRATIONS_FILE, seminars, participants)


def load_talks_for(seminars: List[Seminar]) -> List[Talk]:
    """Загрузить список докладов, связав с уже загруженными семинарами."""
    return load_talks(TALKS_FILE, seminars)
