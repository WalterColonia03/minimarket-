from __future__ import annotations

import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from catalog.models import Product


class InitialInventoryLoad(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.OneToOneField(
        Product,
        on_delete=models.PROTECT,
        related_name="initial_load",
    )
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="initial_inventory_loads",
    )
    confirmed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-confirmed_at"]

    def __str__(self) -> str:
        return f"Carga inicial · {self.product.name}"


class Lot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="lots")
    initial_load = models.ForeignKey(
        InitialInventoryLoad,
        on_delete=models.PROTECT,
        related_name="lots",
    )
    number = models.CharField(max_length=64)
    number_normalized = models.CharField(max_length=64, editable=False)
    initial_quantity = models.PositiveIntegerField()
    available_quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
    )
    expiration_date = models.DateField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["expiration_date", "received_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=("product", "number_normalized"), name="lot_number_unique_per_product"),
            models.CheckConstraint(condition=Q(initial_quantity__gt=0), name="lot_initial_quantity_gt_zero"),
            models.CheckConstraint(condition=Q(available_quantity__gte=0), name="lot_available_quantity_gte_zero"),
            models.CheckConstraint(condition=Q(available_quantity__lte=F("initial_quantity")), name="lot_available_lte_initial"),
            models.CheckConstraint(condition=Q(unit_cost__gt=0), name="lot_unit_cost_gt_zero"),
        ]
        indexes = [models.Index(fields=("product", "expiration_date", "received_at"), name="lot_fefo_idx")]

    @staticmethod
    def normalize_number(value: str) -> str:
        return (value or "").strip().upper()

    def clean(self) -> None:
        super().clean()
        self.number = self.number.strip()
        self.number_normalized = self.normalize_number(self.number)
        if not self.number_normalized:
            raise ValidationError({"number": "Ingrese el número de lote."})
        if self.expiration_date and self.expiration_date <= timezone.localdate():
            raise ValidationError({"expiration_date": "El vencimiento debe ser posterior a hoy en Lima."})
        if self.initial_load_id and self.product_id != self.initial_load.product_id:
            raise ValidationError("El lote y la carga deben pertenecer al mismo producto.")

    def save(self, *args, **kwargs) -> None:
        self.number = self.number.strip()
        self.number_normalized = self.normalize_number(self.number)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.product.name} · {self.number_normalized}"
