"""Представления для страниц регистраций участников."""

from django.http import HttpRequest, HttpResponse

from homepage.render import page
from models.registrations import find_registration_by_id
from webdata import get_registrations


def registration_list(request: HttpRequest) -> HttpResponse:
    """Список всех регистраций."""
    registrations = get_registrations()

    if not registrations:
        content = (
            "<h1 class='mb-3'>Регистрации</h1>" "<p>Регистраций пока нет.</p>"
        )
        return HttpResponse(page("Регистрации", content))

    rows = ""
    for reg in registrations:
        status = "secondary" if reg.is_cancelled else "success"
        status_text = "отменена" if reg.is_cancelled else "активна"
        rows += f"""
        <a href="/registrations/{reg.id}/"
           class="list-group-item list-group-item-action
                  d-flex justify-content-between align-items-center">
            <span>
                <strong>{reg.participant.name}</strong>
                — {reg.seminar.title}
            </span>
            <span class="badge bg-{status}">{status_text}</span>
        </a>
        """

    content = f"""
    <h1 class="mb-3">Регистрации</h1>
    <div class="list-group">{rows}</div>
    """
    return HttpResponse(page("Регистрации", content))


def registration_detail(
    request: HttpRequest, registration_id: int
) -> HttpResponse:
    """Карточка одной регистрации."""
    registrations = get_registrations()
    registration = find_registration_by_id(registrations, registration_id)
    if registration is None:
        content = "<h1>Регистрация не найдена</h1>"
        return HttpResponse(
            page("Регистрация не найдена", content), status=404
        )

    status_text = "Отменена" if registration.is_cancelled else "Активна"

    content = f"""
    <h1 class="mb-3">Регистрация №{registration.id}</h1>
    <p>Участник: {registration.participant.name}
       ({registration.participant.email})</p>
    <p>
        Семинар:
        <a href="/seminars/{registration.seminar.id}/">
            {registration.seminar.title}
        </a>
    </p>
    <p>Статус: {status_text}</p>
    <a href="/registrations/" class="btn btn-secondary mt-3">
        К списку регистраций
    </a>
    """
    return HttpResponse(page(f"Регистрация №{registration.id}", content))
