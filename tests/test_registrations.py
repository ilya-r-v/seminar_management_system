from datetime import date

import pytest

from models.participants import Participant
from models.registrations import create_registration, is_registration_open
from models.seminars import Seminar


def test_registration_creation():
    seminar = Seminar(1, "Лекция", date(2026, 10, 12), 5)
    participant = Participant(1, "Иван", "ivan@example.com")
    registrations = []
    registration = create_registration(registrations, seminar, participant)
    assert registration is not None
    assert registration.seminar is seminar
    assert registration.participant is participant


def test_duplicate_registration_forbidden():
    seminar = Seminar(1, "Лекция", date(2026, 10, 12), 5)
    participant = Participant(1, "Иван", "ivan@example.com")
    registrations = []
    create_registration(registrations, seminar, participant)
    with pytest.raises(ValueError):
        create_registration(registrations, seminar, participant)


def test_cancelled_registration_frees_place():
    seminar = Seminar(1, "Лекция", date(2026, 10, 12), 1)
    participant_a = Participant(1, "Иван", "ivan@example.com")
    participant_b = Participant(2, "Пётр", "petr@example.com")
    registrations = []
    registration = create_registration(registrations, seminar, participant_a)

    assert not is_registration_open(registrations, seminar)
    registration.cancel()
    assert is_registration_open(registrations, seminar)

    new_registration = create_registration(
        registrations, seminar, participant_b
    )
    assert new_registration is not None
