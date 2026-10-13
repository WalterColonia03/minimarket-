from django.contrib import admin

from .models import InitialInventoryLoad, Lot


class LotInline(admin.TabularInline):
    model = Lot
    extra = 0
    readonly_fields = (
        "product",
        "number",
        "number_normalized",
        "initial_quantity",
        "available_quantity",
        "unit_cost",
        "expiration_date",
        "received_at",
    )
    can_delete = False


@admin.register(InitialInventoryLoad)
class InitialInventoryLoadAdmin(admin.ModelAdmin):
    list_display = ("product", "responsible", "confirmed_at")
    readonly_fields = ("product", "responsible", "confirmed_at")
    inlines = (LotInline,)


@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = ("product", "number_normalized", "available_quantity", "unit_cost", "expiration_date")
    search_fields = ("product__name", "number", "number_normalized")
    list_filter = ("expiration_date",)
