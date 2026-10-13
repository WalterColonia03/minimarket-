from __future__ import annotations

import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class CashRegister(models.Model):
    """The single cash register seed; shifts are delivered by HU-CAJA-01."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=32, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.code


class CashShift(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Abierto"
        CLOSED = "CLOSED", "Cerrado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cash_register = models.ForeignKey(CashRegister, on_delete=models.PROTECT, related_name="shifts")
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cash_shifts",
    )
    opening_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    status = models.CharField(max_length=6, choices=Status.choices, default=Status.OPEN)
    opened_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-opened_at"]
        constraints = [
            models.CheckConstraint(condition=Q(opening_amount__gte=0), name="cash_shift_opening_amount_gte_zero"),
            models.CheckConstraint(condition=Q(status__in=("OPEN", "CLOSED")), name="cash_shift_valid_status"),
            models.UniqueConstraint(
                fields=("cash_register",),
                condition=Q(status="OPEN"),
                name="one_open_shift_per_register",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.cash_register.code} · {self.seller.display_name} · {self.status}"
