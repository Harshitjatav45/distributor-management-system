from django.contrib import admin
from ledger.models import Ledger


@admin.register(Ledger)
class LedgerAdmin(admin.ModelAdmin):
    list_display = ('transaction_date', 'reference_type', 'entry_type', 'customer', 'supplier', 'amount', 'balance')
    search_fields = ('customer__customer_name', 'supplier__supplier_name', 'reference_id')
    list_filter = ('reference_type', 'entry_type', 'transaction_date')
    ordering = ('-transaction_date', '-id')
