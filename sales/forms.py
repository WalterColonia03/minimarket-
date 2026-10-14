from __future__ import annotations

from django import forms


class ProductSearchForm(forms.Form):
    query = forms.CharField(
        label="Buscar producto",
        required=False,
        max_length=160,
        widget=forms.TextInput(
            attrs={
                "type": "search",
                "autocomplete": "off",
                "placeholder": "Nombre o código de barras",
            }
        ),
    )


class AddDraftLineForm(forms.Form):
    product_id = forms.UUIDField(widget=forms.HiddenInput)
    quantity = forms.IntegerField(
        label="Cantidad",
        min_value=1,
        widget=forms.NumberInput(attrs={"min": "1", "step": "1", "inputmode": "numeric"}),
    )


class UpdateDraftLineForm(forms.Form):
    quantity = forms.IntegerField(
        label="Cantidad",
        min_value=1,
        widget=forms.NumberInput(attrs={"min": "1", "step": "1", "inputmode": "numeric"}),
    )
