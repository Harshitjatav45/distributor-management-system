from django.contrib import admin
from supplier.models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('supplier_name', 'supplier_code', 'supplier_type', 'city', 'state', 'is_active', 'created_at')
    search_fields = ('supplier_name', 'supplier_code', 'gst_number', 'pan_number')
    list_filter = ('is_active', 'supplier_type', 'state', 'city')
    ordering = ('supplier_name',)
