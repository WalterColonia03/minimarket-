from django.urls import path

from . import views

urlpatterns = [
    path("nuevo/", views.product_create, name="product-entry"),
    path("<uuid:product_id>/registrado/", views.product_created, name="product-created"),
]
