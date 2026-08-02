from django.contrib import admin
from material.models import Material


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('material_name', 'material_code', 'company', 'category', 'selling_price', 'is_active')
    search_fields = ('material_name', 'material_code', 'hsn_code')
    list_filter = ('is_active', 'company', 'category')
    ordering = ('material_name',)
