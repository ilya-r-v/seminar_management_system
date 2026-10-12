"""Маршруты страниц регистраций."""

from django.urls import path

from registrations_app import views

app_name = "registrations"

urlpatterns = [
    path("", views.registration_list, name="list"),
    path(
        "<int:registration_id>/",
        views.registration_detail,
        name="detail",
    ),
]
