from rest_framework import serializers
from company.models import Company


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

    def validate_company_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Company name cannot be blank.")
        return value

    def validate_company_code(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Company code cannot be blank.")
        return value
