from rest_framework import serializers
from customer.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        extra_kwargs = {'customer_code': {'validators': []}}

    def validate_customer_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Customer name cannot be blank.")
        return value

    def validate_customer_code(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Customer code cannot be blank.")
        queryset = Customer.objects.filter(customer_code=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Customer code must be unique.")
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
