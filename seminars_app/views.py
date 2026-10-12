"""Представления для страниц семинаров."""

from typing import List

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from models import Registration, Seminar
from models.seminars import find_seminar_by_id, sort_seminars
from models.talks import get_schedule
from webdata import get_registrations, get_seminars, load_talks_for


def count_active_registrations(
    registrations: List[Registration], seminar: Seminar
) -> int:
    """Посчитать активные регистрации на указанный семинар."""
    return sum(
        1
        for registration in registrations
        if registration.seminar.id == seminar.id
        and not registration.is_cancelled
    )


def seminar_list(request: HttpRequest) -> HttpResponse:
    """Список всех семинаров, отсортированный по дате."""
    registrations = get_registrations()
    seminar_items = []
    for seminar in sort_seminars(get_seminars()):
        registered_count = count_active_registrations(registrations, seminar)
        seminar_items.append(
            {
                "seminar": seminar,
                "registered_count": registered_count,
                "is_full": not seminar.is_available_for(registered_count),
            }
        )
    context = {
        "seminar_items": seminar_items,
    }
    return render(request, "seminars/seminar_list.html", context)


def seminar_detail(request: HttpRequest, seminar_id: int) -> HttpResponse:
    """Страница одного семинара: данные и программа докладов."""
    seminars = get_seminars()
    seminar = find_seminar_by_id(seminars, seminar_id)
    context = {
        "seminar": seminar,
    }
    if seminar is not None:
        registered_count = count_active_registrations(
            get_registrations(), seminar
        )
        context["registered_count"] = registered_count
        context["is_full"] = not seminar.is_available_for(registered_count)
        context["schedule"] = get_schedule(load_talks_for(seminars), seminar)
    return render(
        request,
        "seminars/seminar_detail.html",
        context,
        status=404 if seminar is None else 200,
    )
