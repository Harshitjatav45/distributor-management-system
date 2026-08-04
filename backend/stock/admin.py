from django.contrib import admin
from stock.models import Stock


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('material', 'current_stock', 'reserved_stock', 'available_stock', 'is_active', 'updated_at')
    search_fields = ('material__material_name', 'material__material_code')
    list_filter = ('is_active',)
    ordering = ('material__material_name',)
