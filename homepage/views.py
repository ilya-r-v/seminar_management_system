"""Представления главной страницы сайта."""

from django.http import HttpRequest, HttpResponse

from homepage.render import page
from webdata import get_participants, get_registrations, get_seminars

def page_not_found(
    request: HttpRequest, exception: Exception
) -> HttpResponse:
    """Страница 404 для любых несуществующих адресов."""
    content = """
    <h1 class="mb-3">Страница не найдена</h1>
    <p>Такого адреса на сайте нет.</p>
    <a href="/" class="btn btn-primary">На главную</a>
    """
    return HttpResponse(page("Страница не найдена", content), status=404)


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница: краткая сводка по проекту."""
    seminars = get_seminars()
    participants = get_participants()
    registrations = [r for r in get_registrations() if not r.is_cancelled]

    content = f"""
    <h1 class="mb-3">Система управления семинарами</h1>
    <p class="lead">
        Веб-интерфейс для просмотра семинаров и регистраций участников.
    </p>
    <div class="row g-3 mb-4">
        <div class="col-md-4">
            <div class="card text-center">
                <div class="card-body">
                    <h2>{len(seminars)}</h2>
                    <p class="card-text">Семинаров</p>
                    <a href="/seminars/" class="btn btn-primary btn-sm">
                        Смотреть семинары
                    </a>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card text-center">
                <div class="card-body">
                    <h2>{len(participants)}</h2>
                    <p class="card-text">Участников</p>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card text-center">
                <div class="card-body">
                    <h2>{len(registrations)}</h2>
                    <p class="card-text">Активных регистраций</p>
                    <a href="/registrations/" class="btn btn-primary btn-sm">
                        Смотреть регистрации
                    </a>
                </div>
            </div>
        </div>
    </div>
    """
    return HttpResponse(page("Главная", content))
