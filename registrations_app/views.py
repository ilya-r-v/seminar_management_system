"""Представления для страниц регистраций участников."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from models.registrations import find_registration_by_id
from webdata import get_registrations


def registration_list(request: HttpRequest) -> HttpResponse:
    """Список всех регистраций."""
    context = {
        "registrations": get_registrations(),
    }
    return render(request, "registrations/registration_list.html", context)


def registration_detail(
    request: HttpRequest, registration_id: int
) -> HttpResponse:
    """Страница одной регистрации."""
    registration = find_registration_by_id(
        get_registrations(), registration_id
    )
    context = {
        "registration": registration,
    }
    return render(
        request,
        "registrations/registration_detail.html",
        context,
        status=404 if registration is None else 200,
    )
