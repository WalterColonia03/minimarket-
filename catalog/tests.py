from __future__ import annotations

from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from identity.models import Account, Role

from .models import Category, Product


class CategoryTests(TestCase):
    def test_name_normalization_is_persisted(self) -> None:
        category = Category.objects.create(name=" Productos Enlatados ")
        self.assertEqual(category.name_normalized, "productos enlatados")


class ProductRegistrationTests(TestCase):
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
        cls.category = Category.objects.create(name="Productos enlatados")

    def payload(self, **overrides):
        data = {
            "name": "Atún en agua 170 g",
            "barcode": "7751234567890",
            "category": str(self.category.pk),
            "unit": Product.Unit.UNIT,
            "sale_price": "8.90",
            "minimum_stock": "12",
        }
        data.update(overrides)
        return data

    def test_admin_registers_zero_stock_non_sellable_product(self) -> None:
        self.client.force_login(self.admin)

        response = self.client.post(reverse("product-entry"), self.payload())

        product = Product.objects.get()
        self.assertRedirects(response, reverse("product-created", args=(product.pk,)))
        self.assertEqual(product.category, self.category)
        self.assertEqual(product.unit, Product.Unit.UNIT)
        self.assertEqual(product.sale_price, Decimal("8.90"))
        self.assertEqual(product.minimum_stock, 12)
        self.assertTrue(product.controls_expiration)
        self.assertEqual(product.average_cost, Decimal("0.0000"))
        self.assertEqual(product.physical_stock, 0)
        self.assertEqual(product.sellable_stock, 0)
        self.assertFalse(product.is_sellable)

    def test_omitted_minimum_stock_defaults_to_ten(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(reverse("product-entry"), self.payload(minimum_stock=""))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Product.objects.get().minimum_stock, 10)

    def test_normalized_duplicate_barcode_is_rejected_without_second_row(self) -> None:
        Product.objects.create(
            category=self.category,
            name="Producto previo",
            barcode="775 123 456",
            sale_price=Decimal("3.50"),
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("product-entry"), self.payload(barcode=" 775123456 ")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe un producto con este código de barras")
        self.assertEqual(Product.objects.count(), 1)

    def test_invalid_prices_never_create_product(self) -> None:
        self.client.force_login(self.admin)
        for price in ("0", "-1", "1.999", "texto"):
            with self.subTest(price=price):
                response = self.client.post(reverse("product-entry"), self.payload(sale_price=price))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(Product.objects.count(), 0)

    def test_invalid_minimums_never_create_product(self) -> None:
        self.client.force_login(self.admin)
        for minimum in ("-1", "1.5", "texto"):
            with self.subTest(minimum=minimum):
                response = self.client.post(
                    reverse("product-entry"), self.payload(minimum_stock=minimum)
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(Product.objects.count(), 0)

    def test_inactive_or_wrong_category_is_rejected(self) -> None:
        inactive = Category.objects.create(name="Otra categoría", is_active=False)
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("product-entry"), self.payload(category=str(inactive.pk))
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 0)

    def test_non_admin_post_is_forbidden_and_does_not_create_product(self) -> None:
        for account in (self.warehouse, self.seller):
            with self.subTest(role=account.role.code):
                self.client.force_login(account)
                response = self.client.post(reverse("product-entry"), self.payload())
                self.assertEqual(response.status_code, 403)
                self.assertEqual(Product.objects.count(), 0)

    def test_database_rejects_product_without_expiration_control(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            Product.objects.create(
                category=self.category,
                name="Producto inválido",
                barcode="INVALID-001",
                sale_price=Decimal("2.00"),
                controls_expiration=False,
            )
