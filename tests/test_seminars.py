from datetime import date

from seminars import add_seminar, check_seminar_capacity, find_seminar


def test_add_seminar():
    seminars = {}
    add_seminar(seminars, "Введение в ML", date(2026, 10, 12), 25)
    assert len(seminars) == 1


def test_find_seminar():
    seminars = {}
    add_seminar(seminars, "Введение в ML", date(2026, 10, 12), 25)
    assert find_seminar(seminars, "ml")


def test_check_seminar_capacity():
    seminars = {}
    seminar_id = add_seminar(seminars, "Конференция", date(2026, 11, 1), 50)
    assert check_seminar_capacity(seminars, seminar_id, registered_count=10)
