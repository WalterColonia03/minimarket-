import decimal
import uuid

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalog", "0002_product"),
    ]

    operations = [
        migrations.CreateModel(
            name="InitialInventoryLoad",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("confirmed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "product",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="initial_load",
                        to="catalog.product",
                    ),
                ),
                (
                    "responsible",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="initial_inventory_loads",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-confirmed_at"]},
        ),
        migrations.CreateModel(
            name="Lot",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("number", models.CharField(max_length=64)),
                ("number_normalized", models.CharField(editable=False, max_length=64)),
                ("initial_quantity", models.PositiveIntegerField()),
                ("available_quantity", models.PositiveIntegerField()),
                (
                    "unit_cost",
                    models.DecimalField(
                        decimal_places=4,
                        max_digits=14,
                        validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.0001"))],
                    ),
                ),
                ("expiration_date", models.DateField()),
                ("received_at", models.DateTimeField(auto_now_add=True)),
                (
                    "initial_load",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lots",
                        to="inventory.initialinventoryload",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lots",
                        to="catalog.product",
                    ),
                ),
            ],
            options={
                "ordering": ["expiration_date", "received_at", "id"],
                "indexes": [
                    models.Index(fields=["product", "expiration_date", "received_at"], name="lot_fefo_idx")
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("product", "number_normalized"), name="lot_number_unique_per_product"
                    ),
                    models.CheckConstraint(condition=models.Q(("initial_quantity__gt", 0)), name="lot_initial_quantity_gt_zero"),
                    models.CheckConstraint(condition=models.Q(("available_quantity__gte", 0)), name="lot_available_quantity_gte_zero"),
                    models.CheckConstraint(
                        condition=models.Q(("available_quantity__lte", models.F("initial_quantity"))),
                        name="lot_available_lte_initial",
                    ),
                    models.CheckConstraint(condition=models.Q(("unit_cost__gt", 0)), name="lot_unit_cost_gt_zero"),
                ],
            },
        ),
    ]
