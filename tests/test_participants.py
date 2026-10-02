from models.participants import add_participant, find_participant_by_email


def test_participant_creation():
    participants = []
    participant = add_participant(
        participants, "Иван Петров", "ivan@example.com"
    )
    assert participant.id == 1
    assert participant.name == "Иван Петров"
    assert participant.email == "ivan@example.com"


def test_find_participant_by_email():
    participants = []
    participant = add_participant(participants, "Иван", "ivan@example.com")
    found = find_participant_by_email(participants, "ivan@example.com")
    assert found is participant
