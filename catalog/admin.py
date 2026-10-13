from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name", "name_normalized")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "barcode", "category", "sale_price", "minimum_stock", "is_active")
    list_filter = ("category", "is_active", "controls_expiration")
    search_fields = ("name", "barcode", "barcode_normalized")
    readonly_fields = ("barcode_normalized", "controls_expiration", "average_cost", "created_at", "updated_at")
