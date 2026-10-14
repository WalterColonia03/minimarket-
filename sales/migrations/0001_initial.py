import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("cash", "0002_cashshift"),
        ("catalog", "0002_product"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SaleDraft",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("ACTIVE", "En preparación"), ("DISCARDED", "Descartado")], default="ACTIVE", max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("discarded_at", models.DateTimeField(blank=True, null=True)),
                ("cash_shift", models.ForeignKey(on_delete=models.deletion.PROTECT, related_name="sale_drafts", to="cash.cashshift")),
                ("seller", models.ForeignKey(on_delete=models.deletion.PROTECT, related_name="sale_drafts", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="SaleDraftLine",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("quantity", models.PositiveIntegerField()),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=14, validators=[MinValueValidator(Decimal("0.01"))])),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("draft", models.ForeignKey(on_delete=models.deletion.PROTECT, related_name="lines", to="sales.saledraft")),
                ("product", models.ForeignKey(on_delete=models.deletion.PROTECT, related_name="sale_draft_lines", to="catalog.product")),
            ],
            options={"ordering": ["created_at", "id"]},
        ),
        migrations.AddConstraint(
            model_name="saledraft",
            constraint=models.CheckConstraint(condition=Q(("status__in", ("ACTIVE", "DISCARDED"))), name="sale_draft_valid_status"),
        ),
        migrations.AddConstraint(
            model_name="saledraft",
            constraint=models.UniqueConstraint(condition=Q(("status", "ACTIVE")), fields=("cash_shift",), name="one_active_sale_draft_per_shift"),
        ),
        migrations.AddConstraint(
            model_name="saledraftline",
            constraint=models.CheckConstraint(condition=Q(("quantity__gt", 0)), name="sale_draft_line_quantity_gt_zero"),
        ),
        migrations.AddConstraint(
            model_name="saledraftline",
            constraint=models.CheckConstraint(condition=Q(("unit_price__gt", 0)), name="sale_draft_line_unit_price_gt_zero"),
        ),
        migrations.AddConstraint(
            model_name="saledraftline",
            constraint=models.UniqueConstraint(fields=("draft", "product"), name="sale_draft_line_one_product"),
        ),
    ]
