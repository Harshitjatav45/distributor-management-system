from rest_framework import generics
from audit.models import AuditLog
from audit.serializers import AuditLogSerializer
from accounts.permissions import IsAdminOnly


class AuditLogListAPIView(generics.ListAPIView):
    """Read-only by construction (ListAPIView only - no create/update/
    destroy mixins), so POST/PUT/PATCH/DELETE return 405, not just a
    permission denial. Admin-only: audit history is not exposed to Manager
    or Staff.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminOnly]

    def get_queryset(self):
        qs = AuditLog.objects.all()
        params = self.request.query_params
        model_name = params.get('model_name')
        action = params.get('action')
        object_id = params.get('object_id')
        actor_username = params.get('actor_username')
        if model_name:
            qs = qs.filter(model_name__iexact=model_name)
        if action:
            qs = qs.filter(action__iexact=action)
        if object_id:
            qs = qs.filter(object_id=str(object_id))
        if actor_username:
            qs = qs.filter(actor_username__iexact=actor_username)
        return qs
