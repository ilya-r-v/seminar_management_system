from datetime import date

from models.seminars import Seminar
from models.talks import add_talk, get_schedule, remove_talk


def test_add_talk():
    seminar = Seminar(1, "Лекция", date(2026, 10, 12), 25)
    talks = []
    add_talk(
        talks, seminar, title="Введение", speaker="Иванов",
        start_time="10:00", duration_minutes=30,
    )
    assert len(talks) == 1


def test_get_schedule_sorted_by_time():
    seminar = Seminar(1, "Лекция", date(2026, 10, 12), 25)
    talks = []
    add_talk(
        talks, seminar, title="Доклад Б", speaker="Петров",
        start_time="11:00", duration_minutes=20,
    )
    add_talk(
        talks, seminar, title="Доклад А", speaker="Сидоров",
        start_time="09:30", duration_minutes=20,
    )
    schedule = get_schedule(talks, seminar)
    assert [talk.title for talk in schedule] == ["Доклад А", "Доклад Б"]


def test_remove_talk():
    seminar = Seminar(1, "Лекция", date(2026, 10, 12), 25)
    talks = []
    talk = add_talk(
        talks, seminar, title="Доклад", speaker="Иванов",
        start_time="10:00", duration_minutes=30,
    )
    assert remove_talk(talks, talk.id)
    assert len(talks) == 0
