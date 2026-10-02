from datetime import date

from models.seminars import add_seminar, find_seminar, find_seminar_by_id


def test_seminar_creation():
    seminars = []
    seminar = add_seminar(seminars, "Введение в ML", date(2026, 10, 12), 25)
    assert seminar.id == 1
    assert seminar.title == "Введение в ML"
    assert seminar.max_participants == 25


def test_seminar_is_available_for():
    seminars = []
    seminar = add_seminar(seminars, "Конференция", date(2026, 11, 1), 2)
    assert seminar.is_available_for(1)
    assert not seminar.is_available_for(2)


def test_find_seminar():
    seminars = []
    add_seminar(seminars, "Введение в ML", date(2026, 10, 12), 25)
    assert find_seminar(seminars, "ml")


def test_find_seminar_by_id():
    seminars = []
    seminar = add_seminar(seminars, "Лекция", date(2026, 10, 12), 25)
    assert find_seminar_by_id(seminars, seminar.id) is seminar
