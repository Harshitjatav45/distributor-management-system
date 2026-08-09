from rest_framework import serializers
from dispatch.models import Dispatch
from dispatch.services import VALID_TRANSITIONS


class DispatchSerializer(serializers.ModelSerializer):
    effective_delivery_address = serializers.SerializerMethodField()

    class Meta:
        model = Dispatch
        fields = [
            'id', 'dispatch_number', 'sales', 'dispatch_date', 'status',
            'transport_name', 'vehicle_number', 'lr_number', 'delivery_person',
            'delivery_address', 'effective_delivery_address',
            'expected_delivery_date', 'actual_delivery_date', 'remarks',
            'created_at', 'updated_at',
        ]
        extra_kwargs = {'dispatch_number': {'validators': []}}

    def get_effective_delivery_address(self, obj):
        if obj.delivery_address:
            return obj.delivery_address
        if obj.sales_id and obj.sales.customer:
            return obj.sales.customer.address
        return None

    def validate_dispatch_number(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Dispatch number cannot be blank.")
        queryset = Dispatch.objects.filter(dispatch_number=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Dispatch number must be unique.")
        return value

    def validate(self, attrs):
        if self.instance:
            old_status = self.instance.status
            new_status = attrs.get('status', old_status)
            if old_status != new_status:
                allowed = VALID_TRANSITIONS.get(old_status, set())
                if new_status not in allowed:
                    raise serializers.ValidationError({
                        'status': f"Cannot transition Dispatch from {old_status} to {new_status}."
                    })
        return attrs
