from rest_framework import serializers
from purchase.models import Purchase, PurchaseItem
from material.models import Material


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = '__all__'
        extra_kwargs = {'purchase_number': {'validators': []}}

    def validate_purchase_number(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Purchase number cannot be blank.")
        queryset = Purchase.objects.filter(purchase_number=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Purchase number must be unique.")
        return value


class PurchaseItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseItem
        fields = '__all__'

    def validate_purchase(self, value):
        if not Purchase.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("Purchase does not exist.")
        return value

    def validate_material(self, value):
        if not Material.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("Material does not exist.")
        return value

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

    def validate_actual_weight(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Actual weight cannot be negative.")
        return value

    def validate(self, attrs):
        quantity = attrs.get('quantity', getattr(self.instance, 'quantity', None))
        received_quantity = attrs.get('received_quantity', getattr(self.instance, 'received_quantity', None))

        if received_quantity is not None and quantity is not None and received_quantity > quantity:
            raise serializers.ValidationError("Received quantity cannot be greater than quantity.")

        return attrs
