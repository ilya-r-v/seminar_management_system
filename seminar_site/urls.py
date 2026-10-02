"""Корневая конфигурация маршрутов проекта."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("seminars/", include("seminars_app.urls")),
    path("registrations/", include("registrations_app.urls")),
]
