from django.contrib import admin

from .models import CashRegister, CashShift


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = ("code", "is_active", "created_at")


@admin.register(CashShift)
class CashShiftAdmin(admin.ModelAdmin):
    list_display = ("cash_register", "seller", "opening_amount", "status", "opened_at")
    list_filter = ("status", "cash_register")
    search_fields = ("seller__email", "seller__display_name")
    readonly_fields = ("opened_at",)
