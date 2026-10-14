from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cash.models import CashRegister, CashShift
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot

from .models import SaleDraft, SaleDraftLine


class SalePreparationTests(TestCase):
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
        category = Category.objects.create(name="Productos enlatados")
        cls.product = Product.objects.create(
            category=category,
            name="Atún en lata",
            barcode="775000000001",
            sale_price=Decimal("118.00"),
        )
        load = InitialInventoryLoad.objects.create(product=cls.product, responsible=cls.warehouse)
        cls.sellable_lot = Lot.objects.create(
            product=cls.product,
            initial_load=load,
            number="VIGENTE-01",
            initial_quantity=3,
            available_quantity=3,
            unit_cost=Decimal("40.0000"),
            expiration_date=timezone.localdate() + timedelta(days=20),
        )
        cls.expired_lot = Lot.objects.create(
            product=cls.product,
            initial_load=load,
            number="VENCIDO-01",
            initial_quantity=8,
            available_quantity=8,
            unit_cost=Decimal("40.0000"),
            expiration_date=timezone.localdate(),
        )

    def open_shift(self, seller=None):
        return CashShift.objects.create(
            cash_register=self.cash_register,
            seller=seller or self.seller,
            opening_amount=Decimal("15.00"),
        )

    def add_line(self, quantity="1"):
        return self.client.post(
            reverse("sales-draft"),
            {"product_id": str(self.product.pk), "quantity": quantity},
        )

    def test_empty_preparation_needs_own_open_shift_and_creates_no_draft(self) -> None:
        self.client.force_login(self.seller)

        response = self.client.get(reverse("sales-draft"))

        self.assertContains(response, "Abre tu turno para preparar una venta")
        self.assertFalse(SaleDraft.objects.exists())

    def test_search_finds_active_sellable_product_by_name_or_barcode(self) -> None:
        self.open_shift()
        self.client.force_login(self.seller)

        by_name = self.client.get(reverse("sales-draft"), {"query": "atún"})
        by_code = self.client.get(reverse("sales-draft"), {"query": self.product.barcode})

        self.assertContains(by_name, self.product.name)
        self.assertContains(by_code, self.product.name)
        self.assertContains(by_name, "3")

    def test_first_line_creates_draft_and_does_not_move_stock_or_cash(self) -> None:
        shift = self.open_shift()
        self.client.force_login(self.seller)
        before_quantities = list(Lot.objects.values_list("id", "available_quantity"))

        response = self.add_line("2")

        draft = SaleDraft.objects.get()
        line = SaleDraftLine.objects.get()
        self.assertRedirects(response, f"{reverse('sales-draft')}?query=")
        self.assertEqual(draft.cash_shift, shift)
        self.assertEqual(draft.seller, self.seller)
        self.assertEqual(draft.status, SaleDraft.Status.ACTIVE)
        self.assertEqual(line.quantity, 2)
        self.assertEqual(line.unit_price, Decimal("118.00"))
        self.assertEqual(list(Lot.objects.values_list("id", "available_quantity")), before_quantities)
        shift.refresh_from_db()
        self.assertEqual(shift.opening_amount, Decimal("15.00"))

    def test_same_product_is_grouped_and_cannot_exceed_sellable_stock(self) -> None:
        self.open_shift()
        self.client.force_login(self.seller)
        self.add_line("1")
        self.add_line("1")

        rejected = self.add_line("2")

        self.assertContains(rejected, "supera las existencias vendibles")
        self.assertEqual(SaleDraftLine.objects.count(), 1)
        self.assertEqual(SaleDraftLine.objects.get().quantity, 2)

    def test_expired_or_today_lot_is_not_available_for_preparation(self) -> None:
        self.open_shift()
        self.client.force_login(self.seller)

        response = self.add_line("4")

        self.assertContains(response, "supera las existencias vendibles")
        self.assertFalse(SaleDraft.objects.exists())

    def test_update_and_remove_last_line_discards_draft_without_stock_change(self) -> None:
        self.open_shift()
        self.client.force_login(self.seller)
        self.add_line("1")
        line = SaleDraftLine.objects.get()
        before_quantities = list(Lot.objects.values_list("id", "available_quantity"))

        updated = self.client.post(reverse("sales-line-update", args=(line.pk,)), {"quantity": "3"})
        line.refresh_from_db()
        removed = self.client.post(reverse("sales-line-remove", args=(line.pk,)))

        draft = SaleDraft.objects.get()
        self.assertRedirects(updated, reverse("sales-draft"))
        self.assertEqual(line.quantity, 3)
        self.assertRedirects(removed, reverse("sales-draft"))
        self.assertEqual(draft.status, SaleDraft.Status.DISCARDED)
        self.assertIsNotNone(draft.discarded_at)
        self.assertFalse(SaleDraftLine.objects.exists())
        self.assertEqual(list(Lot.objects.values_list("id", "available_quantity")), before_quantities)

    def test_totals_show_price_base_igv_and_total_with_half_up_rule(self) -> None:
        self.open_shift()
        self.client.force_login(self.seller)
        self.add_line("2")

        response = self.client.get(reverse("sales-draft"))

        self.assertContains(response, "S/ 118,00 por unidad")
        self.assertContains(response, "S/ 200,00")
        self.assertContains(response, "S/ 36,00")
        self.assertContains(response, "S/ 236,00")
        self.assertContains(response, "no descuenta existencias ni mueve efectivo")

    def test_another_seller_cannot_use_the_open_shift_or_create_draft(self) -> None:
        self.open_shift(self.seller)
        self.client.force_login(self.other_seller)

        response = self.add_line("1")

        self.assertContains(response, "turno de caja abierto a tu nombre")
        self.assertFalse(SaleDraft.objects.exists())

    def test_only_seller_role_can_open_the_sales_preparation_route(self) -> None:
        for account in (self.admin, self.warehouse):
            with self.subTest(role=account.role.code):
                self.client.force_login(account)
                response = self.client.get(reverse("sales-draft"))
                self.assertEqual(response.status_code, 403)

    def test_logout_discards_active_draft_but_keeps_shift_and_stock(self) -> None:
        shift = self.open_shift()
        self.client.force_login(self.seller)
        self.add_line("1")
        before_quantities = list(Lot.objects.values_list("id", "available_quantity"))

        confirmation = self.client.get(reverse("logout"))
        response = self.client.post(reverse("logout"))

        draft = SaleDraft.objects.get()
        shift.refresh_from_db()
        self.assertContains(confirmation, "La venta en preparación se descartará")
        self.assertRedirects(response, reverse("login"))
        self.assertEqual(draft.status, SaleDraft.Status.DISCARDED)
        self.assertEqual(shift.status, CashShift.Status.OPEN)
        self.assertEqual(list(Lot.objects.values_list("id", "available_quantity")), before_quantities)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_canceling_logout_keeps_the_session_and_draft(self) -> None:
        self.open_shift()
        self.client.force_login(self.seller)
        self.add_line("1")

        confirmation = self.client.get(reverse("logout"))
        cancel = self.client.get(reverse("dashboard"))

        self.assertContains(confirmation, "La venta en preparación se descartará")
        self.assertEqual(cancel.status_code, 200)
        self.assertTrue(SaleDraft.objects.filter(status=SaleDraft.Status.ACTIVE).exists())
        self.assertIn("_auth_user_id", self.client.session)
