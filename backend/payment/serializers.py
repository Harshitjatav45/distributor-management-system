from rest_framework import serializers
from payment.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        extra_kwargs = {'payment_number': {'validators': []}}

    def validate_payment_number(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Payment number cannot be blank.")
        queryset = Payment.objects.filter(payment_number=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Payment number must be unique.")
        return value

    def validate_amount(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value

    def validate(self, attrs):
        payment_type = attrs.get('payment_type', getattr(self.instance, 'payment_type', None))
        customer = attrs.get('customer', getattr(self.instance, 'customer', None))
        supplier = attrs.get('supplier', getattr(self.instance, 'supplier', None))

        if payment_type == 'PAYMENT_IN':
            if not customer:
                raise serializers.ValidationError({'customer': 'Customer is required for PAYMENT_IN.'})
            if supplier:
                raise serializers.ValidationError({'supplier': 'Supplier must not be set for PAYMENT_IN.'})
        elif payment_type == 'PAYMENT_OUT':
            if not supplier:
                raise serializers.ValidationError({'supplier': 'Supplier is required for PAYMENT_OUT.'})
            if customer:
                raise serializers.ValidationError({'customer': 'Customer must not be set for PAYMENT_OUT.'})

        if self.instance:
            old_status = self.instance.status
            new_status = attrs.get('status', old_status)
            if old_status == 'CANCELLED' and new_status != 'CANCELLED':
                raise serializers.ValidationError(
                    {'status': 'A cancelled payment cannot change status.'}
                )

        return attrs
