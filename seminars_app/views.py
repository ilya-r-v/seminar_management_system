"""Представления для страниц семинаров."""

from django.http import HttpRequest, HttpResponse

from homepage.render import page
from models.seminars import find_seminar_by_id
from models.talks import get_schedule
from webdata import get_registrations, get_seminars, load_talks_for


def seminar_list(request: HttpRequest) -> HttpResponse:
    """Список всех семинаров."""
    seminars = get_seminars()
    registrations = [r for r in get_registrations() if not r.is_cancelled]

    if not seminars:
        content = "<h1 class='mb-3'>Семинары</h1><p>Семинаров пока нет.</p>"
        return HttpResponse(page("Семинары", content))

    rows = ""
    for seminar in sorted(seminars, key=lambda s: s.date):
        registered_count = sum(
            1 for r in registrations if r.seminar.id == seminar.id
        )
        status = (
            "danger"
            if not seminar.is_available_for(registered_count)
            else "success"
        )
        rows += f"""
        <a href="/seminars/{seminar.id}/"
           class="list-group-item list-group-item-action
                  d-flex justify-content-between align-items-center">
            <span>
                <strong>{seminar.title}</strong>
                — {seminar.date.strftime('%d.%m.%Y')}
            </span>
            <span class="badge bg-{status}">
                {registered_count} / {seminar.max_participants}
            </span>
        </a>
        """

    content = f"""
    <h1 class="mb-3">Семинары</h1>
    <div class="list-group">{rows}</div>
    """
    return HttpResponse(page("Семинары", content))


def seminar_detail(request: HttpRequest, seminar_id: int) -> HttpResponse:
    """Карточка одного семинара: данные и программа докладов."""
    seminars = get_seminars()
    seminar = find_seminar_by_id(seminars, seminar_id)
    if seminar is None:
        content = "<h1>Семинар не найден</h1>"
        return HttpResponse(page("Семинар не найден", content), status=404)

    registrations = [r for r in get_registrations() if not r.is_cancelled]
    registered_count = sum(
        1 for r in registrations if r.seminar.id == seminar.id
    )

    talks = load_talks_for(seminars)
    schedule = get_schedule(talks, seminar)
    if schedule:
        talks_html = (
            "<ul class='list-group'>"
            + "".join(
                f"<li class='list-group-item'>{t}</li>" for t in schedule
            )
            + "</ul>"
        )
    else:
        talks_html = "<p>Доклады пока не добавлены.</p>"

    content = f"""
    <h1 class="mb-3">{seminar.title}</h1>
    <p>Дата: {seminar.date.strftime('%d.%m.%Y')}</p>
    <p>
        Занято мест: {registered_count} / {seminar.max_participants}
    </p>
    <h2 class="h5 mt-4">Программа</h2>
    {talks_html}
    <a href="/seminars/" class="btn btn-secondary mt-4">К списку семинаров</a>
    """
    return HttpResponse(page(seminar.title, content))
