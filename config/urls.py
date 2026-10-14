from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("productos/", include("catalog.urls")),
    path("inventario/", include("inventory.urls")),
    path("caja/", include("cash.urls")),
    path("ventas/", include("sales.urls")),
    path("", include("identity.urls")),
]
