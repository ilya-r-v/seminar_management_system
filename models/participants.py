"""Класс Participant и функции работы с коллекцией участников."""
from typing import List, Optional


class Participant:
    """Участник семинаров."""

    def __init__(self, participant_id: int, name: str, email: str) -> None:
        """Создать объект участника."""
        self.id = participant_id
        self.name = name
        self.email = email

    def __str__(self) -> str:
        """Вернуть строковое представление участника."""
        return f"{self.name} <{self.email}>"

    @classmethod
    def from_data(cls, data: dict) -> "Participant":
        """Создать участника из данных, загруженных из JSON."""
        return cls(data["id"], data["name"], data["email"])


def add_participant(
    participants: List[Participant], name: str, email: str
) -> Participant:
    """Создать участника и добавить его в коллекцию."""
    participant_id = max(
        (participant.id for participant in participants), default=0
    ) + 1
    participant = Participant(participant_id, name, email)
    participants.append(participant)
    return participant


def find_participant(
    participants: List[Participant], query: str
) -> List[Participant]:
    """Найти участников по подстроке имени или email."""
    query_lower = query.lower()
    return [
        participant for participant in participants
        if query_lower in participant.name.lower()
        or query_lower in participant.email.lower()
    ]


def find_participant_by_id(
    participants: List[Participant], participant_id: int
) -> Optional[Participant]:
    """Найти участника по идентификатору."""
    for participant in participants:
        if participant.id == participant_id:
            return participant
    return None


def find_participant_by_email(
    participants: List[Participant], email: str
) -> Optional[Participant]:
    """Найти участника по email."""
    for participant in participants:
        if participant.email == email:
            return participant
    return None


def show_participants(participants: List[Participant]) -> None:
    """Вывести список участников."""
    if not participants:
        print("Участников пока нет")
        return
    for participant in participants:
        print(f"{participant.id}. {participant}")
