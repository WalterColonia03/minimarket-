from __future__ import annotations

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from cash.models import CashShift
from catalog.models import Product
from identity.authorization import roles_required
from identity.models import Role

from .forms import AddDraftLineForm, ProductSearchForm, UpdateDraftLineForm
from .services import (
    active_draft_for_actor,
    add_product_to_draft,
    draft_totals,
    remove_draft_line,
    update_draft_line,
)


def _add_validation_error(form, error: ValidationError) -> None:
    if hasattr(error, "error_dict"):
        for field, errors in error.error_dict.items():
            target = field if field in form.fields else None
            for item in errors:
                form.add_error(target, item)
    else:
        for message in error.messages:
            form.add_error(None, message)


def _search_products(query: str):
    if not query:
        return Product.objects.none()
    normalized_code = Product.normalize_barcode(query)
    return (
        Product.objects.filter(is_active=True)
        .filter(Q(name__icontains=query.strip()) | Q(barcode_normalized=normalized_code))
        .filter(lots__available_quantity__gt=0, lots__expiration_date__gt=timezone.localdate())
        .annotate(sellable_quantity=Sum("lots__available_quantity"))
        .order_by("name", "barcode_normalized")
        .distinct()
    )


@roles_required(Role.Code.SELLER)
@never_cache
@require_http_methods(["GET", "POST"])
def sales_draft(request):
    search_form = ProductSearchForm(request.GET or None)
    query = ""
    products = Product.objects.none()
    if search_form.is_valid():
        query = search_form.cleaned_data["query"].strip()
        products = _search_products(query)

    add_form = AddDraftLineForm(request.POST or None)
    if request.method == "POST" and add_form.is_valid():
        try:
            add_product_to_draft(actor=request.user, **add_form.cleaned_data)
        except ValidationError as error:
            _add_validation_error(add_form, error)
        else:
            return redirect(f"{request.path}?query={query}")

    current_shift = CashShift.objects.filter(seller=request.user, status=CashShift.Status.OPEN).first()
    draft = active_draft_for_actor(actor=request.user)
    return render(
        request,
        "sales/sales_draft.html",
        {
            "search_form": search_form,
            "add_form": add_form,
            "query": query,
            "products": products,
            "current_shift": current_shift,
            "draft": draft,
            "totals": draft_totals(draft),
        },
    )


@roles_required(Role.Code.SELLER)
@never_cache
@require_POST
def sales_line_update(request, line_id):
    form = UpdateDraftLineForm(request.POST)
    if form.is_valid():
        try:
            update_draft_line(actor=request.user, line_id=line_id, **form.cleaned_data)
        except ValidationError as error:
            messages.error(request, error.messages[0])
    else:
        messages.error(request, "Ingresa una cantidad entera mayor que cero.")
    return redirect("sales-draft")


@roles_required(Role.Code.SELLER)
@never_cache
@require_POST
def sales_line_remove(request, line_id):
    try:
        remove_draft_line(actor=request.user, line_id=line_id)
    except ValidationError as error:
        messages.error(request, error.messages[0])
    return redirect("sales-draft")
