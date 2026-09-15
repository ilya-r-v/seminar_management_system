from talks import add_talk, get_schedule, remove_talk


def test_add_talk():
    talks = []
    add_talk(
        talks, seminar_id=1, title="Введение", speaker="Иванов",
        start_time="10:00", duration_minutes=30,
    )
    assert len(talks) == 1


def test_get_schedule_sorted_by_time():
    talks = []
    add_talk(
        talks, seminar_id=1, title="Доклад Б", speaker="Петров",
        start_time="11:00", duration_minutes=20,
    )
    add_talk(
        talks, seminar_id=1, title="Доклад А", speaker="Сидоров",
        start_time="09:30", duration_minutes=20,
    )
    schedule = get_schedule(talks, seminar_id=1)
    assert [talk["title"] for talk in schedule] == ["Доклад А", "Доклад Б"]


def test_remove_talk():
    talks = []
    talk = add_talk(
        talks, seminar_id=1, title="Доклад", speaker="Иванов",
        start_time="10:00", duration_minutes=30,
    )
    assert remove_talk(talks, talk["id"])
    assert len(talks) == 0
