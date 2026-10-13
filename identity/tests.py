from __future__ import annotations

from django.contrib.auth.hashers import identify_hasher
from django.test import Client, TestCase
from django.urls import reverse

from .models import Account, Role
from .services import INVALID_CREDENTIALS_MESSAGE


class AuthenticationAndAuthorizationTests(TestCase):
    password = "Test-only-Passw0rd"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        cls.warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        cls.seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
        cls.admin = Account.objects.create_user(
            "admin@test.invalid", cls.password, display_name="Admin", role=cls.admin_role
        )
        cls.warehouse = Account.objects.create_user(
            "warehouse@test.invalid", cls.password, display_name="Almacén", role=cls.warehouse_role
        )
        cls.seller = Account.objects.create_user(
            "seller@test.invalid", cls.password, display_name="Vendedor", role=cls.seller_role
        )
        cls.inactive = Account.objects.create_user(
            "inactive@test.invalid", cls.password, display_name="Inactiva", role=cls.admin_role, is_active=False
        )

    def login(self, email: str, password: str | None = None):
        return self.client.post(reverse("login"), {"email": email, "password": password or self.password})

    def test_active_account_creates_server_session(self) -> None:
        response = self.login(" ADMIN@TEST.INVALID ")
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(str(self.client.session["_auth_user_id"]), str(self.admin.pk))
        self.assertEqual(self.client.session["role_code"], Role.Code.ADMIN)

    def test_login_rotates_an_existing_anonymous_session_key(self) -> None:
        session = self.client.session
        session["pre_auth_marker"] = "kept"
        session.save()
        previous_key = session.session_key

        response = self.login(self.admin.email)

        self.assertRedirects(response, reverse("dashboard"))
        self.assertNotEqual(self.client.session.session_key, previous_key)
        self.assertEqual(self.client.session["pre_auth_marker"], "kept")

    def test_password_uses_argon2_and_is_never_stored_in_plain_text(self) -> None:
        self.assertNotIn(self.password, self.admin.password)
        self.assertEqual(identify_hasher(self.admin.password).algorithm, "argon2")

    def test_login_post_requires_csrf_and_sets_protected_cookies(self) -> None:
        csrf_client = Client(enforce_csrf_checks=True)
        rejected = csrf_client.post(
            reverse("login"), {"email": self.admin.email, "password": self.password}
        )
        self.assertEqual(rejected.status_code, 403)
        self.assertNotIn("_auth_user_id", csrf_client.session)

        form_response = csrf_client.get(reverse("login"))
        csrf_cookie = form_response.cookies["csrftoken"]
        accepted = csrf_client.post(
            reverse("login"),
            {
                "email": self.admin.email,
                "password": self.password,
                "csrfmiddlewaretoken": csrf_cookie.value,
            },
        )

        self.assertRedirects(accepted, reverse("dashboard"))
        self.assertTrue(csrf_cookie["httponly"])
        self.assertEqual(csrf_cookie["samesite"], "Lax")
        self.assertTrue(accepted.cookies["sessionid"]["httponly"])
        self.assertEqual(accepted.cookies["sessionid"]["samesite"], "Lax")

    def test_invalid_email_is_rejected_before_authentication(self) -> None:
        response = self.login("not-an-email")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Introduzca una dirección de correo electrónico válida")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_unknown_email_wrong_password_and_inactive_account_share_message(self) -> None:
        cases = [
            ("unknown@test.invalid", self.password),
            (self.admin.email, "incorrecta"),
            (self.inactive.email, self.password),
        ]
        for email, password in cases:
            with self.subTest(email=email):
                response = self.login(email, password)
                self.assertContains(response, INVALID_CREDENTIALS_MESSAGE)
                self.assertNotIn("_auth_user_id", self.client.session)

    def test_dashboard_only_shows_authorized_navigation(self) -> None:
        self.client.force_login(self.seller)
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Abrir turno")
        self.assertNotContains(response, "Registrar producto")
        self.assertNotContains(response, "Carga inicial")

    def test_direct_operation_is_denied_without_mutating_data(self) -> None:
        self.client.force_login(self.warehouse)
        before = Account.objects.count()
        response = self.client.get(reverse("product-entry"))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Account.objects.count(), before)

    def test_role_matrix_is_enforced_on_direct_urls(self) -> None:
        routes = {
            Role.Code.ADMIN: "product-entry",
            Role.Code.WAREHOUSE: "inventory-load",
            Role.Code.SELLER: "cash-open",
        }
        users = {
            Role.Code.ADMIN: self.admin,
            Role.Code.WAREHOUSE: self.warehouse,
            Role.Code.SELLER: self.seller,
        }
        for allowed_role, route_name in routes.items():
            for current_role, account in users.items():
                with self.subTest(route=route_name, current_role=current_role):
                    self.client.force_login(account)
                    response = self.client.get(reverse(route_name))
                    self.assertEqual(response.status_code, 200 if current_role == allowed_role else 403)

    def test_post_logout_invalidates_session_and_back_route_requires_login(self) -> None:
        self.client.force_login(self.seller)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)
        response = self.client.get(reverse("sales-counter"))
        self.assertEqual(response.status_code, 302)
