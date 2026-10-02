"""Пакет классов предметной области проекта."""
from .participants import Participant
from .registrations import Registration
from .seminars import Seminar
from .talks import Talk

__all__ = ["Seminar", "Participant", "Registration", "Talk"]
