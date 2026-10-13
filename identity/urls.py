from django.urls import path

from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("inicio/", views.dashboard, name="dashboard"),
    path("salir/", views.logout_view, name="logout"),
    path("ventas/", views.sales_counter, name="sales-counter"),
]
