from django.contrib import admin
from company.models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'company_code', 'city', 'state', 'is_active', 'created_at')
    search_fields = ('company_name', 'company_code', 'gst_number', 'pan_number')
    list_filter = ('is_active', 'state', 'city')
    ordering = ('company_name',)
