from django.contrib import admin
from category.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'category_code', 'is_active', 'created_at')
    search_fields = ('category_name', 'category_code')
    list_filter = ('is_active',)
    ordering = ('category_name',)
