from rest_framework import serializers
from category.models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        extra_kwargs = {'category_code': {'validators': []}}

    def validate_category_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Category name cannot be blank.")
        return value

    def validate_category_code(self, value):
        if value:
            queryset = Category.objects.filter(category_code=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("Category code must be unique.")
        return value
