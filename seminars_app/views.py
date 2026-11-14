"""Представления для страниц семинаров (данные через Django ORM)."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from participants_app.models import Participant
from registrations_app.models import Registration
from seminars_app.forms import (
    AvailableSeminarsForm,
    SeminarForm,
    SeminarSearchForm,
)
from seminars_app.models import Seminar


def seminar_list(request: HttpRequest) -> HttpResponse:
    """Список семинаров с поиском по названию."""
    # Форма связана с GET-параметрами: /seminars/?q=...
    # Без параметров форма остаётся несвязанной (пустой).
    form = SeminarSearchForm(request.GET or None)
    query = ""
    # Значение берётся из cleaned_data только после проверки формы.
    if form.is_bound and form.is_valid():
        query = form.cleaned_data["q"]

    # Все семинары с числом занятых и свободных мест.
    seminar_items = Seminar.objects.with_places()

    # Поиск по части названия без учёта регистра.
    if query:
        seminar_items = seminar_items.filter(title__icontains=query)

    # Сортировка: по дате, при равных датах — по названию.
    seminar_items = seminar_items.order_by("seminar_date", "title")

    context = {
        "seminar_items": seminar_items,
        "form": form,
        "query": query,
    }
    return render(request, "seminars/seminar_list.html", context)


def seminar_redirect(request: HttpRequest, seminar_id: int) -> HttpResponse:
    """Перенаправить со старого адреса по номеру на адрес со slug."""
    seminar = get_object_or_404(Seminar, pk=seminar_id)
    # redirect() сам вызывает get_absolute_url() у объекта.
    return redirect(seminar)


def seminar_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Страница одного семинара: данные, программа и участники."""
    # Семинар по текстовому идентификатору; если его нет — ответ 404.
    seminar = get_object_or_404(
        Seminar.objects.with_places(),
        slug=slug,
    )

    # Программа: доклады семинара через обратную связь (related_name).
    schedule = seminar.talks.order_by("start_time")

    # Участники с активной регистрацией на этот семинар:
    # фильтрация по полям связанной модели Registration.
    participants = Participant.objects.filter(
        registrations__seminar=seminar,
        registrations__status=Registration.Status.ACTIVE,
    ).order_by("name")

    context = {
        "seminar": seminar,
        "schedule": schedule,
        "participants": participants,
    }
    return render(request, "seminars/seminar_detail.html", context)


def available_seminars(request: HttpRequest) -> HttpResponse:
    """Поиск семинаров со свободными местами, начиная с выбранной даты."""
    form = AvailableSeminarsForm(request.GET or None)
    selected_date = None
    seminars = []

    # Форма проверяет дату и превращает строку в объект date.
    if form.is_bound and form.is_valid():
        selected_date = form.cleaned_data["date"]
        # Два условия сразу: дата не раньше выбранной
        # и есть хотя бы одно свободное место.
        # Отменённые и завершённые регистрации места не занимают.
        seminars = Seminar.objects.with_places().filter(
            seminar_date__gte=selected_date,
            free_places__gt=0,
        ).order_by("seminar_date")

    context = {
        "form": form,
        "selected_date": selected_date,
        "seminars": seminars,
    }
    return render(request, "seminars/available.html", context)


def seminar_create(request: HttpRequest) -> HttpResponse:
    """Создание семинара через форму (с загрузкой изображения)."""
    if request.method == "POST":
        # Обычные поля приходят в request.POST,
        # загруженный файл — в request.FILES.
        form = SeminarForm(request.POST, request.FILES)
        # Данные сохраняются только после успешной проверки.
        if form.is_valid():
            # save() создаёт запись и сохраняет файл в media/seminars/.
            seminar = form.save()
            # После сохранения — переход на страницу семинара.
            return redirect(seminar)
    else:
        # При GET-запросе показывается пустая форма.
        form = SeminarForm()

    context = {"form": form}
    return render(request, "seminars/seminar_form.html", context)


def seminar_update(request: HttpRequest, slug: str) -> HttpResponse:
    """Редактирование семинара; изображение можно заменить."""
    # Если семинара с таким slug нет — ответ 404.
    seminar = get_object_or_404(Seminar, slug=slug)

    if request.method == "POST":
        # instance связывает форму с существующей записью:
        # save() изменит её, а не создаст новую.
        form = SeminarForm(request.POST, request.FILES, instance=seminar)
        if form.is_valid():
            seminar = form.save()
            return redirect(seminar)
    else:
        # При GET-запросе поля заполнены текущими значениями.
        form = SeminarForm(instance=seminar)

    context = {
        "form": form,
        "seminar": seminar,
    }
    return render(request, "seminars/seminar_form.html", context)
