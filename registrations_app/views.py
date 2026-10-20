"""Представления для страниц регистраций (данные берутся из SQLite)."""

import sqlite3
from typing import List

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.database import fetch_all, fetch_one

# Полная информация о регистрации: вместо идентификаторов выводятся
# название семинара и данные участника (соединение трёх таблиц).
REGISTRATION_SELECT_SQL = """
    SELECT
        registrations.id,
        registrations.is_cancelled,
        seminars.id AS seminar_id,
        seminars.title AS seminar_title,
        strftime('%d.%m.%Y', seminars.seminar_date) AS date_ru,
        participants.name AS participant_name,
        participants.email AS participant_email
    FROM registrations
    JOIN seminars
        ON registrations.seminar_id = seminars.id
    JOIN participants
        ON registrations.participant_id = participants.id
"""

ACTIVE_REGISTRATIONS_SQL = (
    REGISTRATION_SELECT_SQL
    + """
    WHERE registrations.is_cancelled = 0
    ORDER BY seminars.seminar_date, registrations.id;
"""
)

ALL_REGISTRATIONS_SQL = (
    REGISTRATION_SELECT_SQL
    + """
    ORDER BY seminars.seminar_date, registrations.id;
"""
)

REGISTRATION_DETAIL_SQL = (
    REGISTRATION_SELECT_SQL
    + """
    WHERE registrations.id = ?;
"""
)

# Статистика: активные регистрации по семинарам (LEFT JOIN + GROUP BY).
SEMINAR_STATISTICS_SQL = """
    SELECT
        seminars.id,
        seminars.title,
        strftime('%d.%m.%Y', seminars.seminar_date) AS date_ru,
        seminars.max_participants,
        COUNT(registrations.id) AS registrations_count
    FROM seminars
    LEFT JOIN registrations
        ON registrations.seminar_id = seminars.id
        AND registrations.is_cancelled = 0
    GROUP BY
        seminars.id,
        seminars.title,
        seminars.seminar_date,
        seminars.max_participants
    ORDER BY registrations_count DESC, seminars.seminar_date;
"""

# Статистика: активные регистрации по участникам.
PARTICIPANT_STATISTICS_SQL = """
    SELECT
        participants.id,
        participants.name,
        participants.email,
        COUNT(registrations.id) AS registrations_count
    FROM participants
    LEFT JOIN registrations
        ON registrations.participant_id = participants.id
        AND registrations.is_cancelled = 0
    GROUP BY participants.id, participants.name, participants.email
    ORDER BY registrations_count DESC, participants.name;
"""

# Востребованные семинары: заняты не менее половины мест (HAVING).
POPULAR_SEMINARS_SQL = """
    SELECT
        seminars.id,
        seminars.title,
        seminars.max_participants,
        COUNT(registrations.id) AS registrations_count
    FROM seminars
    JOIN registrations
        ON registrations.seminar_id = seminars.id
    WHERE registrations.is_cancelled = 0
    GROUP BY seminars.id, seminars.title, seminars.max_participants
    HAVING COUNT(registrations.id) * 2 >= seminars.max_participants
    ORDER BY registrations_count DESC, seminars.title;
"""

# Участники без активных регистраций (подзапрос NOT IN).
IDLE_PARTICIPANTS_SQL = """
    SELECT
        id,
        name,
        email
    FROM participants
    WHERE id NOT IN (
        SELECT participant_id
        FROM registrations
        WHERE is_cancelled = 0
    )
    ORDER BY name;
"""

ACTIVE_REGISTRATIONS_COUNT_SQL = """
    SELECT COUNT(*) AS registrations_count
    FROM registrations
    WHERE is_cancelled = 0;
"""


def registration_list(request: HttpRequest) -> HttpResponse:
    """Список регистраций: по умолчанию только активные.

    Параметр ?all=1 показывает также отменённые регистрации.
    """
    show_all = request.GET.get("all") == "1"
    registrations: List[sqlite3.Row] = fetch_all(
        ALL_REGISTRATIONS_SQL if show_all else ACTIVE_REGISTRATIONS_SQL
    )
    context = {
        "registrations": registrations,
        "show_all": show_all,
    }
    return render(request, "registrations/registration_list.html", context)


def registration_detail(
    request: HttpRequest, registration_id: int
) -> HttpResponse:
    """Страница одной регистрации."""
    registration = fetch_one(REGISTRATION_DETAIL_SQL, (registration_id,))
    context = {
        "registration": registration,
    }
    return render(
        request,
        "registrations/registration_detail.html",
        context,
        status=404 if registration is None else 200,
    )


def statistics(request: HttpRequest) -> HttpResponse:
    """Статистика регистраций: итоги, группировки и подзапросы."""
    total = fetch_one(ACTIVE_REGISTRATIONS_COUNT_SQL)
    context = {
        "total_registrations": total["registrations_count"] if total else 0,
        "seminar_statistics": fetch_all(SEMINAR_STATISTICS_SQL),
        "participant_statistics": fetch_all(PARTICIPANT_STATISTICS_SQL),
        "popular_seminars": fetch_all(POPULAR_SEMINARS_SQL),
        "idle_participants": fetch_all(IDLE_PARTICIPANTS_SQL),
    }
    return render(request, "registrations/statistics.html", context)
