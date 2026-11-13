"""Представления для страниц регистраций (данные через Django ORM)."""

from datetime import datetime

from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from participants_app.models import Participant
from registrations_app.models import Registration
from seminars_app.models import Seminar

# Сколько регистраций выводить на одной странице списка.
REGISTRATIONS_PER_PAGE = 5

# Разрешённые варианты сортировки: значение параметра sort -> поле.
# Произвольный текст из адреса в order_by() не попадает.
SORT_FIELDS = {
    "date": "seminar__seminar_date",
    "seminar": "seminar__title",
    "participant": "participant__name",
}
DEFAULT_SORT = "date"

# Разрешённые значения фильтра по статусу.
STATUSES = ("active", "cancelled", "all")
DEFAULT_STATUS = "active"


def registration_list(request: HttpRequest) -> HttpResponse:
    """Список регистраций: фильтры, поиск, сортировка, страницы."""
    # Параметры из строки запроса.
    seminar_date = request.GET.get("date", "").strip()
    seminar_id = request.GET.get("seminar", "").strip()
    participant_id = request.GET.get("participant", "").strip()
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    sort = request.GET.get("sort", DEFAULT_SORT).strip()
    error = ""

    # Старая ссылка ?all=1 из ПР7 продолжает работать.
    if not status and request.GET.get("all") == "1":
        status = "all"
    # Неизвестное значение заменяем значением по умолчанию.
    if status not in STATUSES:
        status = DEFAULT_STATUS
    if sort not in SORT_FIELDS:
        sort = DEFAULT_SORT

    registrations = Registration.objects.all()

    # Фильтр по статусу: по умолчанию только активные.
    if status == "active":
        registrations = registrations.filter(is_cancelled=False)
    elif status == "cancelled":
        registrations = registrations.filter(is_cancelled=True)

    # Фильтр по дате семинара (поле связанной модели).
    if seminar_date:
        try:
            selected_date = datetime.strptime(
                seminar_date, "%Y-%m-%d"
            ).date()
        except ValueError:
            error = "Укажите корректную дату."
        else:
            registrations = registrations.filter(
                seminar__seminar_date=selected_date
            )

    # Фильтры по семинару и участнику (внешние ключи).
    # Несколько filter() подряд работают как условие «И».
    if seminar_id.isdigit():
        registrations = registrations.filter(seminar_id=int(seminar_id))
    if participant_id.isdigit():
        registrations = registrations.filter(
            participant_id=int(participant_id)
        )

    # Поиск по нескольким полям: имя или почта участника,
    # либо название семинара (условия объединены через «ИЛИ»).
    if query:
        registrations = registrations.filter(
            Q(participant__name__icontains=query)
            | Q(participant__email__icontains=query)
            | Q(seminar__title__icontains=query)
        )

    # Данные связанных моделей под привычными для шаблона именами,
    # сортировка по выбранному полю (при равенстве — по id)
    # и выбор только нужных шаблону полей.
    registrations = (
        registrations
        .annotate(
            seminar_title=F("seminar__title"),
            seminar_date=F("seminar__seminar_date"),
            participant_name=F("participant__name"),
            participant_email=F("participant__email"),
        )
        .order_by(SORT_FIELDS[sort], "id")
        .values(
            "id",
            "is_cancelled",
            "seminar_id",
            "seminar_title",
            "seminar_date",
            "participant_name",
            "participant_email",
        )
    )

    # Постраничный вывод — после фильтрации и сортировки.
    # get_page() сам обрабатывает неверный номер страницы.
    paginator = Paginator(registrations, REGISTRATIONS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "registrations": page_obj,
        "page_obj": page_obj,
        "selected_date": seminar_date,
        "selected_seminar": seminar_id,
        "selected_participant": participant_id,
        "query": query,
        "status": status,
        "sort": sort,
        "seminars": Seminar.objects.order_by("title"),
        "participants": Participant.objects.order_by("name"),
        "error": error,
    }
    return render(request, "registrations/registration_list.html", context)


def registration_detail(
    request: HttpRequest, registration_id: int
) -> HttpResponse:
    """Страница одной регистрации."""
    # select_related загружает семинар и участника тем же запросом;
    # если регистрации нет — ответ 404.
    registration = get_object_or_404(
        Registration.objects.select_related("seminar", "participant"),
        pk=registration_id,
    )
    context = {
        "registration": registration,
    }
    return render(
        request,
        "registrations/registration_detail.html",
        context,
    )


def statistics(request: HttpRequest) -> HttpResponse:
    """Статистика регистраций: итоги и показатели по группам."""
    # Сводные показатели одним запросом: всего, активных, отменённых.
    totals = Registration.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_cancelled=False)),
        cancelled=Count("id", filter=Q(is_cancelled=True)),
    )

    # Семинары с числом занятых мест (включая семинары без регистраций).
    seminar_statistics = Seminar.objects.with_places().order_by(
        "-registered_count", "seminar_date"
    )

    # Участники с числом активных регистраций
    # (участники без регистраций остаются со значением 0).
    participant_statistics = Participant.objects.annotate(
        registrations_count=Count(
            "registrations",
            filter=Q(registrations__is_cancelled=False),
        ),
    ).order_by("-registrations_count", "name")

    # Востребованные семинары: занято не менее половины мест
    # (аналог HAVING COUNT(...) * 2 >= max_participants из ПР7).
    popular_seminars = (
        Seminar.objects.with_places()
        .annotate(doubled_count=F("registered_count") * 2)
        .filter(
            registered_count__gt=0,
            doubled_count__gte=F("max_participants"),
        )
        .order_by("-registered_count", "title")
    )

    # Участники без активных регистраций:
    # exclude() убирает тех, у кого есть хотя бы одна активная.
    idle_participants = Participant.objects.exclude(
        registrations__is_cancelled=False
    ).order_by("name")

    context = {
        "total_registrations": totals["active"],
        "totals": totals,
        "seminar_statistics": seminar_statistics,
        "participant_statistics": participant_statistics,
        "popular_seminars": popular_seminars,
        "idle_participants": idle_participants,
    }
    return render(request, "registrations/statistics.html", context)
