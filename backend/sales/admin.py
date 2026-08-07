from django.contrib import admin
from sales.models import Sales, SalesItem


@admin.register(Sales)
class SalesAdmin(admin.ModelAdmin):
    list_display = ('sales_number', 'customer', 'sales_date', 'status', 'payment_status', 'grand_total', 'is_active')
    search_fields = ('sales_number', 'invoice_number', 'customer__customer_name', 'customer__customer_code')
    list_filter = ('status', 'payment_status', 'sales_date', 'is_active')
    ordering = ('-sales_date', '-id')


@admin.register(SalesItem)
class SalesItemAdmin(admin.ModelAdmin):
    list_display = ('sales', 'material', 'quantity', 'rate', 'line_total')
    search_fields = ('sales__sales_number', 'material__material_name', 'material__material_code')
    list_filter = ('material',)
    ordering = ('-sales',)
