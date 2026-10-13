import decimal
import uuid

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("cash", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CashShift",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "opening_amount",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.00"))],
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("OPEN", "Abierto"), ("CLOSED", "Cerrado")],
                        default="OPEN",
                        max_length=6,
                    ),
                ),
                ("opened_at", models.DateTimeField(auto_now_add=True)),
                (
                    "cash_register",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="shifts",
                        to="cash.cashregister",
                    ),
                ),
                (
                    "seller",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cash_shifts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-opened_at"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("opening_amount__gte", 0)),
                        name="cash_shift_opening_amount_gte_zero",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("status__in", ("OPEN", "CLOSED"))),
                        name="cash_shift_valid_status",
                    ),
                    models.UniqueConstraint(
                        condition=models.Q(("status", "OPEN")),
                        fields=("cash_register",),
                        name="one_open_shift_per_register",
                    ),
                ],
            },
        )
    ]
