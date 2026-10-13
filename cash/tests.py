from __future__ import annotations

from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from identity.models import Account, Role

from .models import CashRegister, CashShift


class CashOpeningTests(TestCase):
    password = "Test-only-Passw0rd"

    @classmethod
    def setUpTestData(cls) -> None:
        admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
        cls.admin = Account.objects.create_user(
            "admin@test.invalid", cls.password, display_name="Admin", role=admin_role
        )
        cls.warehouse = Account.objects.create_user(
            "warehouse@test.invalid", cls.password, display_name="Almacén", role=warehouse_role
        )
        cls.seller = Account.objects.create_user(
            "seller@test.invalid", cls.password, display_name="Vendedor uno", role=seller_role
        )
        cls.other_seller = Account.objects.create_user(
            "seller2@test.invalid", cls.password, display_name="Vendedor dos", role=seller_role
        )
        cls.cash_register = CashRegister.objects.create(code="CAJA-01")

    def test_seller_opens_zero_amount_shift_linked_to_session(self) -> None:
        self.client.force_login(self.seller)

        response = self.client.post(reverse("cash-open"), {"opening_amount": "0.00"})

        shift = CashShift.objects.get()
        self.assertRedirects(response, reverse("cash-shift-opened", args=(shift.pk,)))
        self.assertEqual(shift.seller, self.seller)
        self.assertEqual(shift.cash_register, self.cash_register)
        self.assertEqual(shift.opening_amount, Decimal("0.00"))
        self.assertEqual(shift.status, CashShift.Status.OPEN)
        self.assertTrue(timezone.is_aware(shift.opened_at))

    def test_invalid_amounts_do_not_create_shift(self) -> None:
        self.client.force_login(self.seller)
        for amount in ("", "-0.01", "1.001", "texto"):
            with self.subTest(amount=amount):
                response = self.client.post(reverse("cash-open"), {"opening_amount": amount})
                self.assertEqual(response.status_code, 200)
                self.assertFalse(CashShift.objects.exists())

    def test_other_roles_cannot_open_shift_by_direct_post(self) -> None:
        for account in (self.admin, self.warehouse):
            with self.subTest(role=account.role.code):
                self.client.force_login(account)
                response = self.client.post(reverse("cash-open"), {"opening_amount": "25.00"})
                self.assertEqual(response.status_code, 403)
                self.assertFalse(CashShift.objects.exists())

    def test_existing_global_open_shift_blocks_another_seller(self) -> None:
        CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=Decimal("10.00"),
        )
        self.client.force_login(self.other_seller)

        response = self.client.post(reverse("cash-open"), {"opening_amount": "20.00"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe un turno abierto")
        self.assertEqual(CashShift.objects.count(), 1)

    def test_database_constraint_rejects_two_open_shifts_for_register(self) -> None:
        CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=Decimal("10.00"),
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            CashShift.objects.create(
                cash_register=self.cash_register,
                seller=self.other_seller,
                opening_amount=Decimal("20.00"),
            )

    def test_seller_cannot_view_another_sellers_shift_detail(self) -> None:
        shift = CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=Decimal("10.00"),
        )
        self.client.force_login(self.other_seller)
        response = self.client.get(reverse("cash-shift-opened", args=(shift.pk,)))
        self.assertEqual(response.status_code, 404)
