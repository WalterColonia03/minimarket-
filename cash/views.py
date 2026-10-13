from __future__ import annotations

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from identity.authorization import roles_required
from identity.models import Role

from .forms import CashOpeningForm
from .models import CashShift
from .services import open_cash_shift


@roles_required(Role.Code.SELLER)
@require_http_methods(["GET", "POST"])
def cash_open(request):
    current_shift = CashShift.objects.select_related("cash_register", "seller").filter(
        status=CashShift.Status.OPEN
    ).first()
    form = CashOpeningForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            shift = open_cash_shift(actor=request.user, **form.cleaned_data)
        except ValidationError as error:
            for message in error.messages:
                form.add_error(None, message)
            current_shift = CashShift.objects.select_related("cash_register", "seller").filter(
                status=CashShift.Status.OPEN
            ).first()
        else:
            return redirect("cash-shift-opened", shift_id=shift.pk)
    return render(
        request,
        "cash/cash_open.html",
        {
            "form": form,
            "current_shift": current_shift,
            "owns_shift": current_shift is not None and current_shift.seller_id == request.user.pk,
        },
    )


@roles_required(Role.Code.SELLER)
@require_GET
def cash_shift_opened(request, shift_id):
    shift = get_object_or_404(
        CashShift.objects.select_related("cash_register", "seller"),
        pk=shift_id,
        seller=request.user,
    )
    return render(request, "cash/cash_shift_opened.html", {"shift": shift})
