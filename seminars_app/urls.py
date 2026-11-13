"""Маршруты страниц семинаров."""

from django.urls import path

from seminars_app import views

app_name = "seminars"

urlpatterns = [
    path("", views.seminar_list, name="list"),
    path("available/", views.available_seminars, name="available"),
    # Старый адрес по номеру (/seminars/1/) перенаправляет на новый.
    path(
        "<int:seminar_id>/",
        views.seminar_redirect,
        name="detail_by_id",
    ),
    # Страница семинара по текстовому идентификатору (slug).
    path("<slug:slug>/", views.seminar_detail, name="detail"),
]
