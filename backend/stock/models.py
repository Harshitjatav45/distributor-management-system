from django.db import models
from material.models import Material


class Stock(models.Model):
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name='stock_records'
    )
    current_stock = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    reserved_stock = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    available_stock = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    last_purchase_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    average_purchase_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.material.material_name
