from django.urls import path

from . import views

urlpatterns = [
    path("abrir/", views.cash_open, name="cash-open"),
    path("turnos/<uuid:shift_id>/abierto/", views.cash_shift_opened, name="cash-shift-opened"),
]
