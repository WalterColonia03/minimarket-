from __future__ import annotations

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from identity.authorization import roles_required
from identity.models import Role

from .forms import InitialLoadProductForm, LotInputFormSet
from .models import InitialInventoryLoad
from .services import LotInput, confirm_initial_load


@roles_required(Role.Code.WAREHOUSE)
@require_http_methods(["GET", "POST"])
def initial_load_create(request):
    product_form = InitialLoadProductForm(request.POST or None)
    lot_formset = LotInputFormSet(request.POST or None, prefix="lots")
    if request.method == "POST" and product_form.is_valid() and lot_formset.is_valid():
        lot_inputs = [LotInput(**form.cleaned_data) for form in lot_formset if form.cleaned_data]
        try:
            load = confirm_initial_load(
                actor=request.user,
                product=product_form.cleaned_data["product"],
                lots=lot_inputs,
            )
        except ValidationError as error:
            for message in error.messages:
                product_form.add_error(None, message)
        else:
            return redirect("inventory-load-created", load_id=load.pk)
    return render(
        request,
        "inventory/initial_load_form.html",
        {"product_form": product_form, "lot_formset": lot_formset},
    )


@roles_required(Role.Code.WAREHOUSE)
@require_GET
def initial_load_created(request, load_id):
    load = get_object_or_404(
        InitialInventoryLoad.objects.select_related("product", "responsible").prefetch_related("lots"),
        pk=load_id,
    )
    return render(request, "inventory/initial_load_created.html", {"load": load})
