from rest_framework import serializers
from material.models import Material


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = '__all__'
        extra_kwargs = {'barcode': {'validators': []}}

    def validate_material_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Material name cannot be blank.")
        return value

    def validate_material_code(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Material code cannot be blank.")
        return value

    def validate_barcode(self, value):
        if value:
            queryset = Material.objects.filter(barcode=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("Barcode must be unique.")
        return value

    def validate(self, attrs):
        purchase_price = attrs.get('purchase_price', getattr(self.instance, 'purchase_price', None))
        selling_price = attrs.get('selling_price', getattr(self.instance, 'selling_price', None))
        mrp = attrs.get('mrp', getattr(self.instance, 'mrp', None))
        gst_percentage = attrs.get('gst_percentage', getattr(self.instance, 'gst_percentage', None))

        if purchase_price is not None and selling_price is not None and selling_price < purchase_price:
            raise serializers.ValidationError("Selling price cannot be less than purchase price.")

        if selling_price is not None and mrp is not None and mrp < selling_price:
            raise serializers.ValidationError("MRP cannot be less than selling price.")

        if gst_percentage is not None and gst_percentage < 0:
            raise serializers.ValidationError("GST percentage cannot be negative.")

        return attrs
