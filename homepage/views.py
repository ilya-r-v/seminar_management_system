"""Представления главной страницы сайта."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from webdata import get_participants, get_registrations, get_seminars


def page_not_found(
    request: HttpRequest, exception: Exception
) -> HttpResponse:
    """Страница 404 для любых несуществующих адресов."""
    return render(request, "404.html", status=404)


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница: краткая сводка по проекту."""
    active_registrations = [
        registration
        for registration in get_registrations()
        if not registration.is_cancelled
    ]
    context = {
        "seminars": get_seminars(),
        "participants": get_participants(),
        "active_registrations": active_registrations,
    }
    return render(request, "homepage/index.html", context)
