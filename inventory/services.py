from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from catalog.models import Product
from identity.models import Account, Role

from .models import InitialInventoryLoad, Lot


@dataclass(frozen=True)
class LotInput:
    number: str
    quantity: int
    unit_cost: Decimal
    expiration_date: date


def _validate_lots(lots: list[LotInput], *, business_date: date) -> list[LotInput]:
    if not lots:
        raise ValidationError("Ingrese al menos un lote.")

    normalized_numbers: set[str] = set()
    validated: list[LotInput] = []
    errors: list[str] = []
    for position, item in enumerate(lots, start=1):
        number = Lot.normalize_number(item.number)
        if not number:
            errors.append(f"Lote {position}: ingrese el número.")
        elif number in normalized_numbers:
            errors.append(f"Lote {position}: el número {number} está repetido.")
        if item.quantity <= 0:
            errors.append(f"Lote {position}: la cantidad debe ser mayor que cero.")
        if item.unit_cost <= 0 or item.unit_cost.as_tuple().exponent < -4:
            errors.append(f"Lote {position}: el costo debe ser mayor que cero y tener hasta cuatro decimales.")
        if item.expiration_date <= business_date:
            errors.append(f"Lote {position}: el vencimiento debe ser posterior a hoy en Lima.")
        normalized_numbers.add(number)
        validated.append(
            LotInput(
                number=number,
                quantity=item.quantity,
                unit_cost=item.unit_cost,
                expiration_date=item.expiration_date,
            )
        )
    if errors:
        raise ValidationError(errors)
    return validated


@transaction.atomic
def confirm_initial_load(
    *,
    actor: Account,
    product: Product,
    lots: list[LotInput],
    business_date: date | None = None,
) -> InitialInventoryLoad:
    """Persist one complete initial load or leave no residue."""
    if not actor.is_authenticated or actor.role.code != Role.Code.WAREHOUSE:
        raise PermissionDenied("No tiene permiso para confirmar cargas de inventario.")

    current_date = business_date or timezone.localdate()
    validated = _validate_lots(lots, business_date=current_date)
    locked_product = Product.objects.select_related("category").select_for_update().get(pk=product.pk)
    if (
        not locked_product.is_active
        or not locked_product.controls_expiration
        or not locked_product.category.is_active
        or locked_product.category.name_normalized != "productos enlatados"
    ):
        raise ValidationError("El producto no está disponible para la carga inicial.")
    if InitialInventoryLoad.objects.filter(product=locked_product).exists():
        raise ValidationError("Este producto ya tiene una carga inicial confirmada.")

    repeated = set(
        Lot.objects.filter(
            product=locked_product,
            number_normalized__in=[item.number for item in validated],
        ).values_list("number_normalized", flat=True)
    )
    if repeated:
        raise ValidationError(f"El lote {sorted(repeated)[0]} ya existe para este producto.")

    try:
        with transaction.atomic():
            load = InitialInventoryLoad.objects.create(product=locked_product, responsible=actor)
            Lot.objects.bulk_create(
                [
                    Lot(
                        product=locked_product,
                        initial_load=load,
                        number=item.number,
                        number_normalized=item.number,
                        initial_quantity=item.quantity,
                        available_quantity=item.quantity,
                        unit_cost=item.unit_cost,
                        expiration_date=item.expiration_date,
                    )
                    for item in validated
                ]
            )
    except IntegrityError as exc:
        raise ValidationError("La carga no pudo confirmarse porque otro intento ya fue registrado.") from exc

    total_quantity = sum(item.quantity for item in validated)
    weighted_total = sum(item.unit_cost * item.quantity for item in validated)
    locked_product.average_cost = (weighted_total / total_quantity).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )
    locked_product.save(update_fields=("average_cost", "updated_at"))
    return load
