"""Представления для страниц семинаров (данные берутся из SQLite)."""

import sqlite3
from datetime import date
from typing import Any, Dict, List

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.database import fetch_all, fetch_one

# Семинары с числом активных регистраций и признаком «мест нет».
# LEFT JOIN сохраняет семинары без регистраций (значение 0).
SEMINARS_SELECT_SQL = """
    SELECT
        seminars.id,
        seminars.title,
        seminars.seminar_date,
        strftime('%d.%m.%Y', seminars.seminar_date) AS date_ru,
        seminars.max_participants,
        COUNT(registrations.id) AS registered_count,
        (
            COUNT(registrations.id) >= seminars.max_participants
        ) AS is_full
    FROM seminars
    LEFT JOIN registrations
        ON registrations.seminar_id = seminars.id
        AND registrations.is_cancelled = 0
"""

SEMINARS_GROUP_SQL = """
    GROUP BY
        seminars.id,
        seminars.title,
        seminars.seminar_date,
        seminars.max_participants
"""

SEMINAR_LIST_SQL = (
    SEMINARS_SELECT_SQL
    + SEMINARS_GROUP_SQL
    + "ORDER BY seminars.seminar_date;"
)

SEMINAR_DETAIL_SQL = (
    SEMINARS_SELECT_SQL
    + "WHERE seminars.id = ?"
    + SEMINARS_GROUP_SQL
    + ";"
)

# Программа семинара: доклады по времени начала.
SCHEDULE_SQL = """
    SELECT
        id,
        title,
        speaker,
        start_time,
        duration_minutes
    FROM talks
    WHERE seminar_id = ?
    ORDER BY start_time;
"""

# Участники семинара: соединение регистраций с участниками.
SEMINAR_PARTICIPANTS_SQL = """
    SELECT
        participants.id,
        participants.name,
        participants.email
    FROM registrations
    JOIN participants
        ON registrations.participant_id = participants.id
    WHERE registrations.seminar_id = ?
      AND registrations.is_cancelled = 0
    ORDER BY participants.name;
"""

# Семинары со свободными местами, начиная с выбранной даты.
AVAILABLE_SEMINARS_SQL = """
    SELECT
        seminars.id,
        seminars.title,
        strftime('%d.%m.%Y', seminars.seminar_date) AS date_ru,
        seminars.max_participants,
        seminars.max_participants
            - COUNT(registrations.id) AS free_places
    FROM seminars
    LEFT JOIN registrations
        ON registrations.seminar_id = seminars.id
        AND registrations.is_cancelled = 0
    WHERE seminars.seminar_date >= ?
    GROUP BY
        seminars.id,
        seminars.title,
        seminars.seminar_date,
        seminars.max_participants
    HAVING COUNT(registrations.id) < seminars.max_participants
    ORDER BY seminars.seminar_date;
"""


def seminar_list(request: HttpRequest) -> HttpResponse:
    """Список всех семинаров, отсортированный по дате."""
    seminar_items: List[sqlite3.Row] = fetch_all(SEMINAR_LIST_SQL)
    context = {
        "seminar_items": seminar_items,
    }
    return render(request, "seminars/seminar_list.html", context)


def seminar_detail(request: HttpRequest, seminar_id: int) -> HttpResponse:
    """Страница одного семинара: данные, программа и участники."""
    seminar = fetch_one(SEMINAR_DETAIL_SQL, (seminar_id,))
    context: Dict[str, Any] = {
        "seminar": seminar,
    }
    if seminar is not None:
        context["schedule"] = fetch_all(SCHEDULE_SQL, (seminar_id,))
        context["participants"] = fetch_all(
            SEMINAR_PARTICIPANTS_SQL, (seminar_id,)
        )
    return render(
        request,
        "seminars/seminar_detail.html",
        context,
        status=404 if seminar is None else 200,
    )


def available_seminars(request: HttpRequest) -> HttpResponse:
    """Поиск семинаров со свободными местами, начиная с выбранной даты."""
    selected_date = request.GET.get("date", "")
    seminars: List[sqlite3.Row] = []
    error = ""
    if selected_date:
        try:
            date.fromisoformat(selected_date)
        except ValueError:
            error = "Укажите дату в формате ГГГГ-ММ-ДД."
        else:
            seminars = fetch_all(AVAILABLE_SEMINARS_SQL, (selected_date,))
    context = {
        "selected_date": selected_date,
        "error": error,
        "seminars": seminars,
    }
    return render(request, "seminars/available.html", context)
