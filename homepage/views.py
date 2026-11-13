"""Представления главной страницы сайта."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from participants_app.models import Participant
from registrations_app.models import Registration
from seminars_app.models import Seminar


def page_not_found(
    request: HttpRequest, exception: Exception
) -> HttpResponse:
    """Страница 404 для любых несуществующих адресов."""
    return render(request, "404.html", status=404)


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница: сводка по данным из базы (Django ORM)."""
    context = {
        "seminars_count": Seminar.objects.count(),
        "participants_count": Participant.objects.count(),
        # Считаем только активные (не отменённые) регистрации.
        "active_registrations_count": Registration.objects.filter(
            is_cancelled=False
        ).count(),
    }
    return render(request, "homepage/index.html", context)
