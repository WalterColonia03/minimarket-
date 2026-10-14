from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Category, Product
from identity.models import Account, Role

from .models import InitialInventoryLoad, Lot
from .services import LotInput, confirm_initial_load


class InitialInventoryLoadTests(TestCase):
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
            "seller@test.invalid", cls.password, display_name="Vendedor", role=seller_role
        )
        category = Category.objects.create(name="Productos enlatados")
        cls.product = Product.objects.create(
            category=category,
            name="Leche evaporada",
            barcode="775000000001",
            sale_price=Decimal("4.80"),
        )

    def payload(self, *, second_expiration=None):
        future_1 = timezone.localdate() + timedelta(days=30)
        future_2 = second_expiration or timezone.localdate() + timedelta(days=60)
        return {
            "product": str(self.product.pk),
            "lots-TOTAL_FORMS": "3",
            "lots-INITIAL_FORMS": "0",
            "lots-MIN_NUM_FORMS": "1",
            "lots-MAX_NUM_FORMS": "1000",
            "lots-0-number": " lote-a ",
            "lots-0-quantity": "2",
            "lots-0-unit_cost": "1.0000",
            "lots-0-expiration_date": future_1.isoformat(),
            "lots-1-number": "Lote-B",
            "lots-1-quantity": "3",
            "lots-1-unit_cost": "2.0000",
            "lots-1-expiration_date": future_2.isoformat(),
            "lots-2-number": "",
            "lots-2-quantity": "",
            "lots-2-unit_cost": "",
            "lots-2-expiration_date": "",
        }

    def test_multiple_lots_are_confirmed_atomically_with_weighted_cost(self) -> None:
        self.client.force_login(self.warehouse)

        response = self.client.post(reverse("inventory-load"), self.payload())

        load = InitialInventoryLoad.objects.get()
        self.assertRedirects(response, reverse("inventory-load-created", args=(load.pk,)))
        confirmation = self.client.get(reverse("inventory-load-created", args=(load.pk,)))
        self.assertEqual(load.responsible, self.warehouse)
        self.assertEqual(Lot.objects.count(), 2)
        self.assertEqual(
            list(Lot.objects.values_list("number_normalized", flat=True)),
            ["LOTE-A", "LOTE-B"],
        )
        for lot in Lot.objects.all():
            self.assertEqual(lot.available_quantity, lot.initial_quantity)
            self.assertTrue(timezone.is_aware(lot.received_at))
        self.product.refresh_from_db()
        self.assertEqual(self.product.physical_stock, 5)
        self.assertEqual(self.product.average_cost, Decimal("1.6000"))
        self.assertTrue(self.product.is_sellable)
        self.assertContains(confirmation, "S/ 1,60")
        self.assertNotContains(confirmation, "S/ 1,6000")

    def test_invalid_middle_lot_rolls_back_entire_load(self) -> None:
        self.client.force_login(self.warehouse)
        response = self.client.post(
            reverse("inventory-load"),
            self.payload(second_expiration=timezone.localdate()),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "posterior a hoy en Lima")
        self.assertEqual(InitialInventoryLoad.objects.count(), 0)
        self.assertEqual(Lot.objects.count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.average_cost, Decimal("0.0000"))

    def test_second_initial_load_is_rejected(self) -> None:
        first = LotInput(
            number="A-1",
            quantity=1,
            unit_cost=Decimal("2.0000"),
            expiration_date=timezone.localdate() + timedelta(days=30),
        )
        confirm_initial_load(actor=self.warehouse, product=self.product, lots=[first])

        with self.assertRaisesMessage(ValidationError, "ya tiene una carga inicial"):
            confirm_initial_load(actor=self.warehouse, product=self.product, lots=[first])
        self.assertEqual(InitialInventoryLoad.objects.count(), 1)
        self.assertEqual(Lot.objects.count(), 1)

    def test_duplicate_numbers_in_same_request_leave_no_residue(self) -> None:
        inputs = [
            LotInput(" lote-1 ", 1, Decimal("1.0000"), timezone.localdate() + timedelta(days=10)),
            LotInput("LOTE-1", 2, Decimal("2.0000"), timezone.localdate() + timedelta(days=20)),
        ]

        with self.assertRaisesMessage(ValidationError, "está repetido"):
            confirm_initial_load(actor=self.warehouse, product=self.product, lots=inputs)
        self.assertFalse(InitialInventoryLoad.objects.exists())
        self.assertFalse(Lot.objects.exists())

    def test_non_warehouse_post_is_forbidden_without_mutation(self) -> None:
        for account in (self.admin, self.seller):
            with self.subTest(role=account.role.code):
                self.client.force_login(account)
                response = self.client.post(reverse("inventory-load"), self.payload())
                self.assertEqual(response.status_code, 403)
                self.assertFalse(InitialInventoryLoad.objects.exists())
                self.assertFalse(Lot.objects.exists())
