"""Функции для работы с докладами и формирования расписания семинара."""


def add_talk(
    talks: list[dict],
    seminar_id: int,
    title: str,
    speaker: str,
    start_time: str,
    duration_minutes: int,
) -> dict:
    """Добавить доклад в программу семинара."""
    talk_id = max((t["id"] for t in talks), default=0) + 1
    talk = {
        "id": talk_id,
        "seminar_id": seminar_id,
        "title": title,
        "speaker": speaker,
        "start_time": start_time,
        "duration_minutes": duration_minutes,
    }
    talks.append(talk)
    return talk


def remove_talk(talks: list[dict], talk_id: int) -> bool:
    """Удалить доклад из программы по идентификатору."""
    for index, talk in enumerate(talks):
        if talk["id"] == talk_id:
            del talks[index]
            return True
    return False


def get_schedule(talks: list[dict], seminar_id: int) -> list[dict]:
    """Сформировать расписание докладов, отсортированное по времени."""
    seminar_talks = [
        talk for talk in talks if talk["seminar_id"] == seminar_id
    ]
    return sorted(seminar_talks, key=lambda talk: talk["start_time"])
