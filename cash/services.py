from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from identity.models import Account, Role

from .models import CashRegister, CashShift


@transaction.atomic
def open_cash_shift(*, actor: Account, opening_amount: Decimal) -> CashShift:
    """Open the seeded cash register for the authenticated seller."""
    if not actor.is_authenticated or actor.role.code != Role.Code.SELLER:
        raise PermissionDenied("No tiene permiso para abrir caja.")
    if opening_amount < 0 or opening_amount.as_tuple().exponent < -2:
        raise ValidationError({"opening_amount": "Ingrese un monto no negativo con hasta dos decimales."})

    cash_register = (
        CashRegister.objects.select_for_update().filter(is_active=True, code="CAJA-01").first()
    )
    if cash_register is None:
        raise ValidationError("La caja única CAJA-01 no está disponible.")
    if CashShift.objects.filter(status=CashShift.Status.OPEN).exists():
        raise ValidationError("Ya existe un turno abierto. Cierre ese turno antes de abrir otro.")

    try:
        with transaction.atomic():
            return CashShift.objects.create(
                cash_register=cash_register,
                seller=actor,
                opening_amount=opening_amount,
                status=CashShift.Status.OPEN,
            )
    except IntegrityError as exc:
        raise ValidationError("Otro vendedor abrió la caja antes de completar este intento.") from exc
