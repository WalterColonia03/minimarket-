from __future__ import annotations

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from identity.authorization import roles_required
from identity.models import Role

from .forms import ProductRegistrationForm
from .models import Product
from .services import register_canned_product


def _attach_validation_error(form, error: ValidationError) -> None:
    if hasattr(error, "error_dict"):
        for field, errors in error.error_dict.items():
            target = field if field in form.fields else None
            for item in errors:
                form.add_error(target, item)
    else:
        for item in error.error_list:
            form.add_error(None, item)


@roles_required(Role.Code.ADMIN)
@require_http_methods(["GET", "POST"])
def product_create(request):
    form = ProductRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            product = register_canned_product(actor=request.user, **form.cleaned_data)
        except ValidationError as error:
            _attach_validation_error(form, error)
        else:
            return redirect("product-created", product_id=product.pk)
    return render(request, "catalog/product_form.html", {"form": form})


@roles_required(Role.Code.ADMIN)
@require_GET
def product_created(request, product_id):
    product = get_object_or_404(Product.objects.select_related("category"), pk=product_id)
    return render(request, "catalog/product_created.html", {"product": product})

