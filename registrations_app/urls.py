"""Маршруты страниц регистраций."""

from django.urls import path

from registrations_app import views

app_name = "registrations"

# Статические маршруты (statistics/, create/) стоят выше маршрутов
# с параметром <int:registration_id>.
urlpatterns = [
    path("", views.registration_list, name="list"),
    path("statistics/", views.statistics, name="statistics"),
    # Форма создания регистрации.
    path("create/", views.registration_create, name="create"),
    path(
        "<int:registration_id>/",
        views.registration_detail,
        name="detail",
    ),
    # Форма редактирования регистрации.
    path(
        "<int:registration_id>/edit/",
        views.registration_update,
        name="update",
    ),
    # Отмена регистрации (принимает только POST).
    path(
        "<int:registration_id>/cancel/",
        views.registration_cancel,
        name="cancel",
    ),
]
