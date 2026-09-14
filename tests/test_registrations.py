import pytest

from registrations import create_registration, is_registration_open


def test_is_registration_open():
    registrations = []
    assert is_registration_open(
        registrations, seminar_id=1, max_participants=5
    )


def test_duplicate_registration_forbidden():
    registrations = []
    create_registration(registrations, seminar_id=1, participant_name="Иван")
    with pytest.raises(ValueError):
        create_registration(
            registrations, seminar_id=1, participant_name="Иван"
        )


def test_registration_closes_at_capacity():
    registrations = []
    create_registration(registrations, seminar_id=1, participant_name="Иван")
    assert not is_registration_open(
        registrations, seminar_id=1, max_participants=1
    )