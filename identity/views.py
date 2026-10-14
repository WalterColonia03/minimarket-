from __future__ import annotations

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from .forms import LoginForm
from .services import INVALID_CREDENTIALS_MESSAGE, authenticate_active_account, create_server_session


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        result = authenticate_active_account(form.cleaned_data["email"], form.cleaned_data["password"])
        if result.authenticated:
            create_server_session(request, result.account)
            return redirect("dashboard")
        form.add_error(None, INVALID_CREDENTIALS_MESSAGE)
    return render(request, "identity/login.html", {"form": form})


@login_required
@require_GET
@never_cache
def dashboard(request):
    return render(request, "identity/dashboard.html")


@login_required
@require_http_methods(["GET", "POST"])
@never_cache
def logout_view(request):
    from sales.services import active_draft_for_actor, discard_active_draft

    draft = active_draft_for_actor(actor=request.user)
    if request.method == "POST":
        if draft is not None:
            discard_active_draft(actor=request.user)
        logout(request)
        return redirect("login")
    return render(request, "identity/logout_confirm.html", {"has_active_draft": draft is not None})
