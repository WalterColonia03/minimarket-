from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone

from cash.models import CashShift
from catalog.models import Product
from identity.models import Account, Role
from inventory.models import Lot

from .models import SaleDraft, SaleDraftLine

MONEY = Decimal("0.01")
IGV_FACTOR = Decimal("1.18")


@dataclass(frozen=True)
class DraftTotals:
    total: Decimal
    base: Decimal
    igv: Decimal


def _require_seller(actor: Account) -> None:
    if not actor.is_authenticated or actor.role.code != Role.Code.SELLER:
        raise PermissionDenied("No tiene permiso para preparar ventas.")


def _own_open_shift(*, actor: Account, lock: bool = False) -> CashShift:
    queryset = CashShift.objects.select_related("seller")
    if lock:
        queryset = queryset.select_for_update()
    shift = queryset.filter(seller=actor, status=CashShift.Status.OPEN).first()
    if shift is None:
        raise ValidationError("Necesitas un turno de caja abierto a tu nombre para preparar una venta.")
    return shift


def sellable_stock_for_product(product: Product) -> int:
    """Return stock usable today in Lima, without reserving or modifying lots."""
    return (
        Lot.objects.filter(
            product=product,
            available_quantity__gt=0,
            expiration_date__gt=timezone.localdate(),
        ).aggregate(quantity=Sum("available_quantity"))["quantity"]
        or 0
    )


def active_draft_for_actor(*, actor: Account) -> SaleDraft | None:
    if not actor.is_authenticated or actor.role.code != Role.Code.SELLER:
        return None
    return (
        SaleDraft.objects.filter(seller=actor, status=SaleDraft.Status.ACTIVE)
        .select_related("cash_shift")
        .prefetch_related("lines__product")
        .first()
    )


def draft_totals(draft: SaleDraft | None) -> DraftTotals:
    total = Decimal("0.00")
    if draft is not None:
        total = sum((line.amount for line in draft.lines.all()), start=total).quantize(MONEY)
    base = (total / IGV_FACTOR).quantize(MONEY, rounding=ROUND_HALF_UP)
    return DraftTotals(total=total, base=base, igv=total - base)


@transaction.atomic
def add_product_to_draft(*, actor: Account, product_id, quantity: int) -> SaleDraft:
    """Add a valid product without moving stock or cash."""
    _require_seller(actor)
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        raise ValidationError({"quantity": "Ingrese una cantidad entera mayor que cero."})

    shift = _own_open_shift(actor=actor, lock=True)
    product = Product.objects.filter(pk=product_id, is_active=True).first()
    if product is None:
        raise ValidationError("El producto seleccionado no está disponible para la venta.")
    available = sellable_stock_for_product(product)
    if available <= 0:
        raise ValidationError("El producto no tiene existencias vendibles disponibles.")

    draft = (
        SaleDraft.objects.select_for_update()
        .filter(cash_shift=shift, status=SaleDraft.Status.ACTIVE)
        .first()
    )
    try:
        if draft is None:
            if quantity > available:
                raise ValidationError({"quantity": "La cantidad supera las existencias vendibles disponibles."})
            draft = SaleDraft.objects.create(cash_shift=shift, seller=actor)
            SaleDraftLine.objects.create(draft=draft, product=product, quantity=quantity, unit_price=product.sale_price)
        else:
            line = SaleDraftLine.objects.select_for_update().filter(draft=draft, product=product).first()
            final_quantity = quantity if line is None else line.quantity + quantity
            if final_quantity > available:
                raise ValidationError({"quantity": "La cantidad supera las existencias vendibles disponibles."})
            if line is None:
                SaleDraftLine.objects.create(
                    draft=draft,
                    product=product,
                    quantity=quantity,
                    unit_price=product.sale_price,
                )
            else:
                line.quantity = final_quantity
                line.unit_price = product.sale_price
                line.save(update_fields=("quantity", "unit_price", "updated_at"))
    except IntegrityError as exc:
        raise ValidationError("No se pudo preparar la venta. Inténtalo nuevamente.") from exc
    return draft


@transaction.atomic
def update_draft_line(*, actor: Account, line_id, quantity: int) -> SaleDraft:
    _require_seller(actor)
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        raise ValidationError({"quantity": "Ingrese una cantidad entera mayor que cero."})
    line = (
        SaleDraftLine.objects.select_for_update()
        .select_related("draft", "draft__cash_shift", "product")
        .filter(pk=line_id, draft__seller=actor, draft__status=SaleDraft.Status.ACTIVE)
        .first()
    )
    if line is None:
        raise ValidationError("La línea de venta ya no está disponible.")
    shift = _own_open_shift(actor=actor, lock=True)
    if line.draft.cash_shift_id != shift.pk:
        raise ValidationError("La línea no pertenece a tu turno abierto.")
    available = sellable_stock_for_product(line.product)
    if quantity > available:
        raise ValidationError({"quantity": "La cantidad supera las existencias vendibles disponibles."})
    line.quantity = quantity
    line.unit_price = line.product.sale_price
    line.save(update_fields=("quantity", "unit_price", "updated_at"))
    return line.draft


@transaction.atomic
def remove_draft_line(*, actor: Account, line_id) -> None:
    _require_seller(actor)
    line = (
        SaleDraftLine.objects.select_for_update()
        .select_related("draft", "draft__cash_shift")
        .filter(pk=line_id, draft__seller=actor, draft__status=SaleDraft.Status.ACTIVE)
        .first()
    )
    if line is None:
        raise ValidationError("La línea de venta ya no está disponible.")
    shift = _own_open_shift(actor=actor, lock=True)
    if line.draft.cash_shift_id != shift.pk:
        raise ValidationError("La línea no pertenece a tu turno abierto.")
    draft = line.draft
    line.delete()
    if not SaleDraftLine.objects.filter(draft=draft).exists():
        draft.status = SaleDraft.Status.DISCARDED
        draft.discarded_at = timezone.now()
        draft.save(update_fields=("status", "discarded_at", "updated_at"))


@transaction.atomic
def discard_active_draft(*, actor: Account) -> bool:
    """Discard the seller draft; cash shifts and lots remain untouched."""
    _require_seller(actor)
    draft = (
        SaleDraft.objects.select_for_update()
        .filter(seller=actor, status=SaleDraft.Status.ACTIVE)
        .first()
    )
    if draft is None:
        return False
    draft.status = SaleDraft.Status.DISCARDED
    draft.discarded_at = timezone.now()
    draft.save(update_fields=("status", "discarded_at", "updated_at"))
    return True
