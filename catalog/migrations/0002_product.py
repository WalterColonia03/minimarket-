import decimal
import uuid

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=160)),
                ("barcode", models.CharField(max_length=64)),
                ("barcode_normalized", models.CharField(editable=False, max_length=64, unique=True)),
                (
                    "unit",
                    models.CharField(choices=[("UND", "Unidad (UND)")], default="UND", max_length=3),
                ),
                (
                    "sale_price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.01"))],
                    ),
                ),
                ("minimum_stock", models.PositiveIntegerField(default=10)),
                ("controls_expiration", models.BooleanField(default=True, editable=False)),
                (
                    "average_cost",
                    models.DecimalField(
                        decimal_places=4,
                        default=decimal.Decimal("0.0000"),
                        max_digits=14,
                        validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.0000"))],
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="products",
                        to="catalog.category",
                    ),
                ),
            ],
            options={
                "ordering": ["name", "barcode_normalized"],
                "constraints": [
                    models.CheckConstraint(condition=models.Q(("sale_price__gt", 0)), name="product_sale_price_gt_zero"),
                    models.CheckConstraint(condition=models.Q(("minimum_stock__gte", 0)), name="product_minimum_stock_gte_zero"),
                    models.CheckConstraint(condition=models.Q(("average_cost__gte", 0)), name="product_average_cost_gte_zero"),
                    models.CheckConstraint(condition=models.Q(("controls_expiration", True)), name="product_requires_expiration"),
                    models.CheckConstraint(condition=models.Q(("unit", "UND")), name="product_unit_und_in_r1"),
                ],
            },
        )
    ]
