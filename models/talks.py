"""Класс Talk и функции работы с докладами и расписанием семинара."""
from typing import List

from .seminars import Seminar


class Talk:
    """Доклад в программе семинара."""

    def __init__(
        self,
        talk_id: int,
        seminar: Seminar,
        title: str,
        speaker: str,
        start_time: str,
        duration_minutes: int,
    ) -> None:
        """Создать объект доклада."""
        self.id = talk_id
        self.seminar = seminar
        self.title = title
        self.speaker = speaker
        self.start_time = start_time
        self.duration_minutes = duration_minutes

    def __str__(self) -> str:
        """Вернуть строковое представление доклада."""
        return (
            f"{self.start_time} — {self.title} "
            f"({self.speaker}, {self.duration_minutes} мин)"
        )


def add_talk(
    talks: List[Talk],
    seminar: Seminar,
    title: str,
    speaker: str,
    start_time: str,
    duration_minutes: int,
) -> Talk:
    """Добавить доклад в программу семинара."""
    talk_id = max((talk.id for talk in talks), default=0) + 1
    talk = Talk(
        talk_id, seminar, title, speaker, start_time, duration_minutes
    )
    talks.append(talk)
    return talk


def remove_talk(talks: List[Talk], talk_id: int) -> bool:
    """Удалить доклад из программы по идентификатору."""
    for index, talk in enumerate(talks):
        if talk.id == talk_id:
            del talks[index]
            return True
    return False


def get_schedule(talks: List[Talk], seminar: Seminar) -> List[Talk]:
    """Сформировать расписание докладов семинара по времени начала."""
    seminar_talks = [
        talk for talk in talks if talk.seminar.id == seminar.id
    ]
    return sorted(seminar_talks, key=lambda talk: talk.start_time)


def show_schedule(talks: List[Talk], seminar: Seminar) -> None:
    """Вывести расписание докладов семинара."""
    schedule = get_schedule(talks, seminar)
    if not schedule:
        print("Доклады пока не добавлены")
        return
    for talk in schedule:
        print(talk)
