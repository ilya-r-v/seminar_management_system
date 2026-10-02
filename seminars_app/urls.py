"""Маршруты страниц семинаров."""

from django.urls import path

from seminars_app import views

urlpatterns = [
    path("", views.seminar_list, name="seminar_list"),
    path("<int:seminar_id>/", views.seminar_detail, name="seminar_detail"),
]
