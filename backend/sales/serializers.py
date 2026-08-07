from rest_framework import serializers
from sales.models import Sales, SalesItem


class SalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sales
        fields = '__all__'
        extra_kwargs = {'sales_number': {'validators': []}}

    def validate_sales_number(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Sales number cannot be blank.")
        queryset = Sales.objects.filter(sales_number=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Sales number must be unique.")
        return value

    def validate_total_amount(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Total amount cannot be negative.")
        return value

    def validate_discount_amount(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Discount amount cannot be negative.")
        return value

    def validate_gst_amount(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("GST amount cannot be negative.")
        return value

    def validate_grand_total(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Grand total cannot be negative.")
        return value


class SalesItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesItem
        fields = '__all__'

    def validate_quantity(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value

    def validate_rate(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Rate cannot be negative.")
        return value

    def validate_discount_percentage(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Discount percentage cannot be negative.")
        return value

    def validate_gst_percentage(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("GST percentage cannot be negative.")
        return value
