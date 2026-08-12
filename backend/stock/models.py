from django.core.validators import MinValueValidator
from django.db import models
from material.models import Material


class Stock(models.Model):
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name='stock_records'
    )
    current_stock = models.DecimalField(max_digits=12, decimal_places=3, default=0, validators=[MinValueValidator(0)])
    reserved_stock = models.DecimalField(max_digits=12, decimal_places=3, default=0, validators=[MinValueValidator(0)])
    available_stock = models.DecimalField(max_digits=12, decimal_places=3, default=0, validators=[MinValueValidator(0)])
    last_purchase_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    average_purchase_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # DB-level defense-in-depth mirroring the existing serializer
        # validation (stock/serializers.py) - never trust only the API
        # layer for financial/inventory integrity.
        constraints = [
            models.CheckConstraint(condition=models.Q(current_stock__gte=0), name='stock_current_stock_gte_0'),
            models.CheckConstraint(condition=models.Q(reserved_stock__gte=0), name='stock_reserved_stock_gte_0'),
            models.CheckConstraint(condition=models.Q(available_stock__gte=0), name='stock_available_stock_gte_0'),
            models.CheckConstraint(
                condition=models.Q(last_purchase_price__isnull=True) | models.Q(last_purchase_price__gte=0),
                name='stock_last_purchase_price_gte_0',
            ),
            models.CheckConstraint(
                condition=models.Q(average_purchase_price__isnull=True) | models.Q(average_purchase_price__gte=0),
                name='stock_average_purchase_price_gte_0',
            ),
            models.CheckConstraint(condition=models.Q(reserved_stock__lte=models.F('current_stock')), name='stock_reserved_lte_current'),
            models.CheckConstraint(condition=models.Q(available_stock__lte=models.F('current_stock')), name='stock_available_lte_current'),
        ]

    def __str__(self):
        return self.material.material_name
