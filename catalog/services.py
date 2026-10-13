from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from identity.models import Account, Role

from .models import Category, Product


@transaction.atomic
def register_canned_product(
    *,
    actor: Account,
    name: str,
    barcode: str,
    category: Category,
    unit: str,
    sale_price,
    minimum_stock: int | None,
) -> Product:
    """Register a zero-stock canned product with server-side authorization."""
    if not actor.is_authenticated or actor.role.code != Role.Code.ADMIN:
        raise PermissionDenied("No tiene permiso para registrar productos.")

    product = Product(
        name=name,
        barcode=barcode,
        barcode_normalized=Product.normalize_barcode(barcode),
        category=category,
        unit=unit,
        sale_price=sale_price,
        minimum_stock=10 if minimum_stock is None else minimum_stock,
        controls_expiration=True,
    )
    # The database remains the final arbiter for the normalized unique code,
    # which also closes the race between two simultaneous registrations.
    product.full_clean(validate_unique=False)
    try:
        with transaction.atomic():
            product.save(force_insert=True)
    except IntegrityError as exc:
        if Product.objects.filter(barcode_normalized=Product.normalize_barcode(barcode)).exists():
            raise ValidationError({"barcode": "Ya existe un producto con este código de barras."}) from exc
        raise
    return product
