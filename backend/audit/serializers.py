from rest_framework import serializers
from audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            'id', 'actor_username', 'action', 'model_name', 'object_id',
            'object_repr', 'before_state', 'after_state', 'metadata', 'timestamp',
        ]
        read_only_fields = fields
