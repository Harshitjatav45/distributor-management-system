from django.contrib import admin
from customer.models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'customer_code', 'customer_type', 'city', 'state', 'is_active', 'created_at')
    search_fields = ('customer_name', 'customer_code', 'gst_number', 'pan_number')
    list_filter = ('is_active', 'customer_type', 'state', 'city')
    ordering = ('customer_name',)
