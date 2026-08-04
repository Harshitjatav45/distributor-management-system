from rest_framework import serializers
from stock.models import Stock


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = '__all__'

    def validate_current_stock(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Current stock cannot be negative.")
        return value

    def validate_reserved_stock(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Reserved stock cannot be negative.")
        return value

    def validate_available_stock(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Available stock cannot be negative.")
        return value

    def validate_last_purchase_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Last purchase price cannot be negative.")
        return value

    def validate_average_purchase_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Average purchase price cannot be negative.")
        return value

    def validate(self, attrs):
        current_stock = attrs.get('current_stock', getattr(self.instance, 'current_stock', None))
        reserved_stock = attrs.get('reserved_stock', getattr(self.instance, 'reserved_stock', None))
        available_stock = attrs.get('available_stock', getattr(self.instance, 'available_stock', None))

        if reserved_stock is not None and current_stock is not None and reserved_stock > current_stock:
            raise serializers.ValidationError("Reserved stock cannot be greater than current stock.")

        if available_stock is not None and current_stock is not None and available_stock > current_stock:
            raise serializers.ValidationError("Available stock cannot be greater than current stock.")

        return attrs
