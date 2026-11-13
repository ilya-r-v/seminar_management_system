"""Представления для страниц семинаров (данные через Django ORM)."""

from datetime import datetime

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from participants_app.models import Participant
from seminars_app.models import Seminar


def seminar_list(request: HttpRequest) -> HttpResponse:
    """Список семинаров с поиском по названию."""
    # Поисковый запрос из строки адреса: /seminars/?q=...
    query = request.GET.get("q", "").strip()

    # Все семинары с числом занятых и свободных мест.
    seminar_items = Seminar.objects.with_places()

    # Поиск по части названия без учёта регистра.
    if query:
        seminar_items = seminar_items.filter(title__icontains=query)

    # Сортировка: по дате, при равных датах — по названию.
    seminar_items = seminar_items.order_by("seminar_date", "title")

    context = {
        "seminar_items": seminar_items,
        "query": query,
    }
    return render(request, "seminars/seminar_list.html", context)


def seminar_detail(request: HttpRequest, seminar_id: int) -> HttpResponse:
    """Страница одного семинара: данные, программа и участники."""
    # Семинар по первичному ключу; если его нет — ответ 404.
    seminar = get_object_or_404(
        Seminar.objects.with_places(),
        pk=seminar_id,
    )

    # Программа: доклады семинара через обратную связь (related_name).
    schedule = seminar.talks.order_by("start_time")

    # Участники с активной регистрацией на этот семинар:
    # фильтрация по полям связанной модели Registration.
    participants = Participant.objects.filter(
        registrations__seminar=seminar,
        registrations__is_cancelled=False,
    ).order_by("name")

    context = {
        "seminar": seminar,
        "schedule": schedule,
        "participants": participants,
    }
    return render(request, "seminars/seminar_detail.html", context)


def available_seminars(request: HttpRequest) -> HttpResponse:
    """Поиск семинаров со свободными местами, начиная с выбранной даты."""
    selected_date = request.GET.get("date", "").strip()
    seminars = []
    error = ""

    if selected_date:
        try:
            # Проверяем ввод: строка должна быть датой ГГГГ-ММ-ДД.
            search_date = datetime.strptime(
                selected_date, "%Y-%m-%d"
            ).date()
        except ValueError:
            error = "Укажите дату в формате ГГГГ-ММ-ДД."
        else:
            # Два условия сразу: дата не раньше выбранной
            # и есть хотя бы одно свободное место.
            # Отменённые регистрации места не занимают.
            seminars = Seminar.objects.with_places().filter(
                seminar_date__gte=search_date,
                free_places__gt=0,
            ).order_by("seminar_date")

    context = {
        "selected_date": selected_date,
        "error": error,
        "seminars": seminars,
    }
    return render(request, "seminars/available.html", context)
