from django.urls import path

from . import views

urlpatterns = [
    path("carga-inicial/", views.initial_load_create, name="inventory-load"),
    path("cargas/<uuid:load_id>/", views.initial_load_created, name="inventory-load-created"),
]
