"""Представления главной страницы сайта."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.database import fetch_one

SEMINARS_COUNT_SQL = """
    SELECT COUNT(*) AS seminars_count
    FROM seminars;
"""

PARTICIPANTS_COUNT_SQL = """
    SELECT COUNT(*) AS participants_count
    FROM participants;
"""

ACTIVE_REGISTRATIONS_COUNT_SQL = """
    SELECT COUNT(*) AS registrations_count
    FROM registrations
    WHERE is_cancelled = 0;
"""


def page_not_found(
    request: HttpRequest, exception: Exception
) -> HttpResponse:
    """Страница 404 для любых несуществующих адресов."""
    return render(request, "404.html", status=404)


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница: сводка по данным из базы SQLite."""
    seminars = fetch_one(SEMINARS_COUNT_SQL)
    participants = fetch_one(PARTICIPANTS_COUNT_SQL)
    registrations = fetch_one(ACTIVE_REGISTRATIONS_COUNT_SQL)
    context = {
        "seminars_count": seminars["seminars_count"] if seminars else 0,
        "participants_count": (
            participants["participants_count"] if participants else 0
        ),
        "active_registrations_count": (
            registrations["registrations_count"] if registrations else 0
        ),
    }
    return render(request, "homepage/index.html", context)
