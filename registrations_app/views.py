"""Представления для страниц регистраций (данные через Django ORM)."""

from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from participants_app.models import Participant
from registrations_app.forms import (
    RegistrationFilterForm,
    RegistrationForm,
)
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

# Статус по умолчанию: в списке показываются активные регистрации.
DEFAULT_STATUS = Registration.Status.ACTIVE.value

# Сообщение об отсутствии мест (общая ошибка формы).
NO_PLACES_ERROR = "На выбранном семинаре нет свободных мест."


def registration_list(request: HttpRequest) -> HttpResponse:
    """Список регистраций: фильтры, поиск, сортировка, страницы."""
    # Форма связана с GET-параметрами запроса. Если параметров нет,
    # передаётся None и форма остаётся несвязанной (пустой).
    form = RegistrationFilterForm(request.GET or None)
    # Форма проверяется один раз, результат используется ниже.
    form_valid = form.is_bound and form.is_valid()

    # Значения по умолчанию. Если форма не прошла проверку,
    # фильтрация по непроверенным значениям не выполняется.
    query = ""
    seminar = None
    participant = None
    seminar_date = None
    status = DEFAULT_STATUS
    sort = DEFAULT_SORT
    error = None

    if form_valid:
        # cleaned_data содержит проверенные и преобразованные значения:
        # дату (date), объекты Seminar и Participant, строки.
        query = form.cleaned_data["q"]
        seminar = form.cleaned_data["seminar"]
        participant = form.cleaned_data["participant"]
        seminar_date = form.cleaned_data["date"]
        status = form.cleaned_data["status"] or DEFAULT_STATUS
        sort = form.cleaned_data["sort"] or DEFAULT_SORT
    elif form.is_bound:
        # Общее сообщение; ошибки отдельных полей выводит шаблон.
        error = "Проверьте введённые значения фильтров."

    # Фильтр по статусу: по умолчанию только активные.
    # Методы active(), cancelled(), completed() описаны в менеджере
    # модели, поэтому правило отбора хранится в одном месте.
    if status == Registration.Status.ACTIVE:
        registrations = Registration.objects.active()
    elif status == Registration.Status.CANCELLED:
        registrations = Registration.objects.cancelled()
    elif status == Registration.Status.COMPLETED:
        registrations = Registration.objects.completed()
    else:
        registrations = Registration.objects.all()

    # Фильтр по дате семинара (поле связанной модели).
    if seminar_date:
        registrations = registrations.for_date(seminar_date)

    # Фильтры по семинару и участнику (внешние ключи).
    # Несколько filter() подряд работают как условие «И».
    if seminar:
        registrations = registrations.filter(seminar=seminar)
    if participant:
        registrations = registrations.filter(participant=participant)

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
            "status",
            "seminar_id",
            "seminar_title",
            "seminar_date",
            "participant_name",
            "participant_email",
        )
    )

    # Постраничный вывод — после фильтрации и сортировки.
    # Номер страницы не относится к условиям фильтрации,
    # поэтому он читается из запроса напрямую, а не через форму.
    # get_page() сам обрабатывает неверный номер страницы.
    paginator = Paginator(registrations, REGISTRATIONS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "registrations": page_obj,
        "page_obj": page_obj,
        "form": form,
        "status": status,
        "sort": sort,
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


def seminar_has_free_place(seminar, registration=None):
    """Проверить, есть ли на семинаре свободное место.

    Считаются только активные регистрации: отменённые и завершённые
    места не занимают. При редактировании передаётся сама регистрация,
    чтобы она не считалась занятым местом и не мешала самой себе.
    """
    occupied = Registration.objects.active().filter(seminar=seminar)
    if registration is not None:
        occupied = occupied.exclude(pk=registration.pk)
    return occupied.count() < seminar.max_participants


def registration_create(request: HttpRequest) -> HttpResponse:
    """Создание регистрации через форму."""
    if request.method == "POST":
        # Форма связана с данными, которые отправил пользователь.
        form = RegistrationForm(request.POST)
        # is_valid() запускает проверки полей, clean_seminar() и clean().
        if form.is_valid():
            seminar = form.cleaned_data["seminar"]
            # Правило предметной области: мест должно хватать.
            if seminar_has_free_place(seminar):
                # Статус не приходит из формы: новая регистрация
                # получает значение по умолчанию «активна».
                registration = form.save()
                # После сохранения — переход на карточку регистрации.
                return redirect(
                    "registrations:detail",
                    registration_id=registration.pk,
                )
            # Общая ошибка формы, не связанная с отдельным полем.
            form.add_error(None, NO_PLACES_ERROR)
    else:
        # При GET-запросе показывается пустая форма. Если в адресе
        # передан семинар (?seminar=3), он подставляется как начальное
        # значение: так работает кнопка на странице семинара.
        initial = {}
        seminar_id = request.GET.get("seminar", "")
        if seminar_id.isdigit():
            initial["seminar"] = int(seminar_id)
        form = RegistrationForm(initial=initial)

    context = {"form": form}
    return render(request, "registrations/registration_form.html", context)


def registration_update(
    request: HttpRequest, registration_id: int
) -> HttpResponse:
    """Редактирование активной регистрации."""
    # Изменять можно только активные регистрации: для отменённых,
    # завершённых и несуществующих вернётся ответ 404.
    registration = get_object_or_404(
        Registration.objects.active(),
        pk=registration_id,
    )

    if request.method == "POST":
        # instance связывает форму с существующей записью:
        # save() изменит её, а не создаст новую.
        form = RegistrationForm(request.POST, instance=registration)
        if form.is_valid():
            seminar = form.cleaned_data["seminar"]
            # Сама редактируемая регистрация из подсчёта исключается.
            if seminar_has_free_place(seminar, registration):
                form.save()
                return redirect(
                    "registrations:detail",
                    registration_id=registration.pk,
                )
            form.add_error(None, NO_PLACES_ERROR)
    else:
        # При GET-запросе поля заполнены текущими значениями.
        form = RegistrationForm(instance=registration)

    context = {
        "form": form,
        "registration": registration,
    }
    return render(request, "registrations/registration_form.html", context)


@require_POST
def registration_cancel(
    request: HttpRequest, registration_id: int
) -> HttpResponse:
    """Отмена регистрации (только POST-запросом).

    Запись не удаляется: её статус меняется на «отменена»,
    а место на семинаре освобождается.
    """
    # Отменить можно только активную регистрацию, иначе — ответ 404.
    registration = get_object_or_404(
        Registration.objects.active(),
        pk=registration_id,
    )
    # Метод модели меняет статус и сохраняет его в базе.
    registration.cancel()
    return redirect("registrations:list")


def statistics(request: HttpRequest) -> HttpResponse:
    """Статистика регистраций: итоги и показатели по группам."""
    # Сводные показатели одним запросом: всего и по каждому статусу.
    totals = Registration.objects.aggregate(
        total=Count("id"),
        active=Count(
            "id", filter=Q(status=Registration.Status.ACTIVE)
        ),
        cancelled=Count(
            "id", filter=Q(status=Registration.Status.CANCELLED)
        ),
        completed=Count(
            "id", filter=Q(status=Registration.Status.COMPLETED)
        ),
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
            filter=Q(registrations__status=Registration.Status.ACTIVE),
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
        registrations__status=Registration.Status.ACTIVE
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
