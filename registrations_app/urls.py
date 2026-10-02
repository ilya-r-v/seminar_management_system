"""Маршруты страниц регистраций."""

from django.urls import path

from registrations_app import views

urlpatterns = [
    path("", views.registration_list, name="registration_list"),
    path(
        "<int:registration_id>/",
        views.registration_detail,
        name="registration_detail",
    ),
]
