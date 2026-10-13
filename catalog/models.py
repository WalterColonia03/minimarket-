from __future__ import annotations

import unicodedata
import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Category(models.Model):
    """Foundation category needed by the R1 product registration flow."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    name_normalized = models.CharField(max_length=120, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name_normalized"]

    def save(self, *args, **kwargs) -> None:
        self.name = self.name.strip()
        self.name_normalized = self.name.casefold()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    """Canned product registered by HU-PROD-02.

    Stock is intentionally derived from lots.  There is no editable stock field,
    which prevents product registration from making an item sellable by itself.
    """

    class Unit(models.TextChoices):
        UNIT = "UND", "Unidad (UND)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=160)
    barcode = models.CharField(max_length=64)
    barcode_normalized = models.CharField(max_length=64, unique=True, editable=False)
    unit = models.CharField(max_length=3, choices=Unit.choices, default=Unit.UNIT)
    sale_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    minimum_stock = models.PositiveIntegerField(default=10)
    controls_expiration = models.BooleanField(default=True, editable=False)
    average_cost = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=Decimal("0.0000"),
        validators=[MinValueValidator(Decimal("0.0000"))],
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "barcode_normalized"]
        constraints = [
            models.CheckConstraint(condition=Q(sale_price__gt=0), name="product_sale_price_gt_zero"),
            models.CheckConstraint(condition=Q(minimum_stock__gte=0), name="product_minimum_stock_gte_zero"),
            models.CheckConstraint(condition=Q(average_cost__gte=0), name="product_average_cost_gte_zero"),
            models.CheckConstraint(condition=Q(controls_expiration=True), name="product_requires_expiration"),
            models.CheckConstraint(condition=Q(unit="UND"), name="product_unit_und_in_r1"),
        ]

    @staticmethod
    def normalize_barcode(value: str) -> str:
        normalized = unicodedata.normalize("NFKC", value or "")
        return "".join(normalized.split()).casefold()

    def clean(self) -> None:
        super().clean()
        self.name = self.name.strip()
        self.barcode = self.barcode.strip()
        self.barcode_normalized = self.normalize_barcode(self.barcode)
        if not self.name:
            raise ValidationError({"name": "Ingrese el nombre del producto."})
        if not self.barcode_normalized:
            raise ValidationError({"barcode": "Ingrese el código de barras."})
        if self.category_id and (
            not self.category.is_active or self.category.name_normalized != "productos enlatados"
        ):
            raise ValidationError({"category": "Seleccione la categoría activa Productos enlatados."})
        if not self.controls_expiration:
            raise ValidationError({"controls_expiration": "El control de vencimiento es obligatorio para este producto."})

    def save(self, *args, **kwargs) -> None:
        self.name = self.name.strip()
        self.barcode = self.barcode.strip()
        self.barcode_normalized = self.normalize_barcode(self.barcode)
        super().save(*args, **kwargs)

    @property
    def physical_stock(self) -> int:
        if not hasattr(self, "lots"):
            return 0
        return sum(self.lots.values_list("available_quantity", flat=True))

    @property
    def sellable_stock(self) -> int:
        if not hasattr(self, "lots"):
            return 0
        return sum(
            self.lots.filter(expiration_date__gt=timezone.localdate()).values_list(
                "available_quantity", flat=True
            )
        )

    @property
    def is_sellable(self) -> bool:
        return self.is_active and self.sellable_stock > 0

    def __str__(self) -> str:
        return f"{self.name} ({self.barcode})"
