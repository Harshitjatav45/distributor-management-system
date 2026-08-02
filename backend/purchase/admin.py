from django.contrib import admin
from purchase.models import Purchase, PurchaseItem


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('purchase_number', 'supplier', 'purchase_date', 'status', 'payment_status', 'grand_total', 'is_active')
    search_fields = ('purchase_number', 'invoice_number', 'supplier__supplier_name')
    list_filter = ('status', 'payment_status', 'is_active')
    ordering = ('-purchase_date',)


@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ('purchase', 'material', 'quantity', 'unit', 'rate', 'line_total')
    search_fields = ('purchase__purchase_number', 'material__material_name', 'batch_number', 'hsn_code_snapshot')
    list_filter = ('purchase__status', 'unit')
    ordering = ('-created_at',)
