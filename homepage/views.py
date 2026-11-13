"""Представления главной страницы сайта."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from participants_app.models import Participant
from registrations_app.models import Registration


def page_not_found(
    request: HttpRequest, exception: Exception
) -> HttpResponse:
    """Страница 404 для любых несуществующих адресов."""
    return render(request, "404.html", status=404)


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница: сводка по данным из базы (Django ORM)."""
    context = {
        # Число семинаров приходит из контекстного процессора
        # (переменная seminars_total), здесь его считать не нужно.
        "participants_count": Participant.objects.count(),
        # Считаем только активные регистрации.
        "active_registrations_count": (
            Registration.objects.active().count()
        ),
    }
    return render(request, "homepage/index.html", context)
