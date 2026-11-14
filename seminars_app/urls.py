"""Маршруты страниц семинаров."""

from django.urls import path

from seminars_app import views

app_name = "seminars"

# Статические маршруты (available/, create/) стоят выше маршрутов
# с параметрами, иначе слово create было бы принято за slug.
urlpatterns = [
    path("", views.seminar_list, name="list"),
    path("available/", views.available_seminars, name="available"),
    # Форма создания семинара.
    path("create/", views.seminar_create, name="create"),
    # Старый адрес по номеру (/seminars/1/) перенаправляет на новый.
    path(
        "<int:seminar_id>/",
        views.seminar_redirect,
        name="detail_by_id",
    ),
    # Форма редактирования семинара.
    path("<slug:slug>/edit/", views.seminar_update, name="update"),
    # Страница семинара по текстовому идентификатору (slug).
    path("<slug:slug>/", views.seminar_detail, name="detail"),
]
