from decimal import Decimal

from django import forms


class CashOpeningForm(forms.Form):
    opening_amount = forms.DecimalField(
        label="Monto inicial (S/)",
        min_value=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "min": "0.00",
                "step": "0.01",
                "inputmode": "decimal",
                "autofocus": True,
                "placeholder": "0.00",
            }
        ),
    )
