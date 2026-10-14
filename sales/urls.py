from django.urls import path

from . import views

urlpatterns = [
    path("", views.sales_draft, name="sales-draft"),
    path("lineas/<uuid:line_id>/", views.sales_line_update, name="sales-line-update"),
    path("lineas/<uuid:line_id>/quitar/", views.sales_line_remove, name="sales-line-remove"),
]
