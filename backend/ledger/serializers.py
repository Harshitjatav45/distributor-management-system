from rest_framework import serializers
from ledger.models import Ledger


class LedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ledger
        fields = '__all__'

    def validate_amount(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value

    def validate_balance(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Balance cannot be negative.")
        return value

    def validate_reference_id(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Reference ID must be greater than 0 if provided.")
        return value

    def validate(self, attrs):
        customer = attrs.get('customer', getattr(self.instance, 'customer', None))
        supplier = attrs.get('supplier', getattr(self.instance, 'supplier', None))

        if customer and supplier:
            raise serializers.ValidationError("Only one of customer or supplier can be provided, not both.")

        if not customer and not supplier:
            raise serializers.ValidationError("Either customer or supplier must be provided.")

        return attrs
