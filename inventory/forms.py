from __future__ import annotations

from decimal import Decimal

from django import forms
from django.forms import formset_factory

from catalog.models import Product


class InitialLoadProductForm(forms.Form):
    product = forms.ModelChoiceField(
        label="Producto sin carga inicial",
        queryset=Product.objects.none(),
        empty_label="Seleccione un producto",
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(
            is_active=True,
            controls_expiration=True,
            initial_load__isnull=True,
        ).select_related("category")


class LotInputForm(forms.Form):
    number = forms.CharField(label="Número de lote", max_length=64)
    quantity = forms.IntegerField(
        label="Cantidad",
        min_value=1,
        widget=forms.NumberInput(attrs={"min": "1", "step": "1", "inputmode": "numeric"}),
    )
    unit_cost = forms.DecimalField(
        label="Costo unitario (S/)",
        min_value=Decimal("0.0001"),
        max_digits=14,
        decimal_places=4,
        widget=forms.NumberInput(attrs={"min": "0.0001", "step": "0.0001", "inputmode": "decimal"}),
    )
    expiration_date = forms.DateField(
        label="Vencimiento",
        widget=forms.DateInput(attrs={"type": "date"}),
    )


LotInputFormSet = formset_factory(LotInputForm, extra=3, min_num=1, validate_min=True)
