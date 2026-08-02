from rest_framework import serializers
from supplier.models import Supplier


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'
        extra_kwargs = {'supplier_code': {'validators': []}}

    def validate_supplier_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Supplier name cannot be blank.")
        return value

    def validate_supplier_code(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Supplier code cannot be blank.")
        queryset = Supplier.objects.filter(supplier_code=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Supplier code must be unique.")
        return value

    def validate_opening_balance(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Opening balance cannot be negative.")
        return value

    def validate_credit_limit(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Credit limit cannot be negative.")
        return value

    def validate_credit_days(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Credit days cannot be negative.")
        return value
