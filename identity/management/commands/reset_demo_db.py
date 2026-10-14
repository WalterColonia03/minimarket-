"""Reset the demo database to a clean seeded state.

Only allowed in APP_ENV=local or APP_ENV=demo. Blocked in production.
Deletes all business data (roles, accounts, categories, cash registers,
sessions) and re-runs seed_pmv to restore the baseline fixture.

Usage:
    SEED_ADMIN_PASSWORD=... SEED_WAREHOUSE_PASSWORD=... SEED_SELLER_PASSWORD=... \\
    python manage.py reset_demo_db [--confirm]
"""
from __future__ import annotations

import os

from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from cash.models import CashRegister, CashShift
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot
from sales.models import SaleDraft, SaleDraftLine


_ALLOWED_ENVS = {"local", "demo"}


class Command(BaseCommand):
    help = (
        "Wipes all business data and re-seeds the demo baseline. "
        "Blocked in production. Requires --confirm flag."
    )

    def add_arguments(self, parser) -> None:  # type: ignore[override]
        parser.add_argument(
            "--confirm",
            action="store_true",
            default=False,
            help="Required safety flag to execute the reset (prevents accidental runs).",
        )

    def handle(self, *args, **options) -> None:
        app_env = os.environ.get("APP_ENV", "local")

        if app_env not in _ALLOWED_ENVS:
            raise CommandError(
                f"reset_demo_db is not allowed in APP_ENV={app_env!r}. "
                f"Only allowed in: {sorted(_ALLOWED_ENVS)}."
            )

        if not options["confirm"]:
            raise CommandError(
                "Safety flag missing. Run with --confirm to execute the reset."
            )

        self.stdout.write("Resetting demo database…")

        with transaction.atomic():
            # Delete in FK-safe order: dependents first.
            Session.objects.all().delete()
            SaleDraftLine.objects.all().delete()
            SaleDraft.objects.all().delete()
            Lot.objects.all().delete()
            InitialInventoryLoad.objects.all().delete()
            CashShift.objects.all().delete()
            Product.objects.all().delete()
            Account.objects.all().delete()
            Role.objects.all().delete()
            Category.objects.all().delete()
            CashRegister.objects.all().delete()

            # Verify tables are empty before re-seeding.
            counts = {
                "roles": Role.objects.count(),
                "accounts": Account.objects.count(),
                "categories": Category.objects.count(),
                "products": Product.objects.count(),
                "initial_loads": InitialInventoryLoad.objects.count(),
                "lots": Lot.objects.count(),
                "cash_registers": CashRegister.objects.count(),
                "cash_shifts": CashShift.objects.count(),
                "sale_drafts": SaleDraft.objects.count(),
                "sale_draft_lines": SaleDraftLine.objects.count(),
            }
            non_zero = {k: v for k, v in counts.items() if v != 0}
            if non_zero:
                raise CommandError(
                    f"Unexpected rows after deletion (aborting): {non_zero}"
                )

            # Re-seed inside the same transaction so any failure rolls back the wipe.
            call_command("seed_pmv", stdout=self.stdout)

        self.stdout.write(
            self.style.SUCCESS(
                "Demo database reset complete: all business data wiped and re-seeded."
            )
        )
