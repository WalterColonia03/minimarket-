from __future__ import annotations

from django import forms

from .models import Category, Product


class ProductRegistrationForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("name", "barcode", "category", "unit", "sale_price", "minimum_stock")
        labels = {
            "name": "Nombre del producto",
            "barcode": "Código de barras",
            "category": "Categoría",
            "unit": "Unidad de medida",
            "sale_price": "Precio final con IGV (S/)",
            "minimum_stock": "Existencia mínima",
        }
        help_texts = {
            "barcode": "Debe ser único. Se ignorarán espacios exteriores e internos al compararlo.",
            "sale_price": "Mayor que cero y con un máximo de dos decimales.",
            "minimum_stock": "Entero mayor o igual que cero. Si lo deja vacío, se guardará 10.",
        }
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "off", "autofocus": True}),
            "barcode": forms.TextInput(attrs={"autocomplete": "off", "inputmode": "numeric"}),
            "sale_price": forms.NumberInput(attrs={"min": "0.01", "step": "0.01", "inputmode": "decimal"}),
            "minimum_stock": forms.NumberInput(attrs={"min": "0", "step": "1", "inputmode": "numeric"}),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(
            is_active=True, name_normalized="productos enlatados"
        )
        self.fields["minimum_stock"].required = False

    def clean_minimum_stock(self) -> int:
        value = self.cleaned_data.get("minimum_stock")
        return 10 if value is None else value

    def clean_barcode(self) -> str:
        value = self.cleaned_data["barcode"]
        normalized = Product.normalize_barcode(value)
        if Product.objects.filter(barcode_normalized=normalized).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe un producto con este código de barras.")
        return value
