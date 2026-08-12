from django.db import transaction
from audit.services import write_audit


class AuditedMasterDataMixin:
    """Mixin for master-data ListCreateAPIView / RetrieveUpdateDestroyAPIView
    subclasses (Company, Category, Material, Supplier, Customer). Audits
    CREATE, UPDATE, and DELETE. Set `audit_repr_field` to the model's
    human-readable name field.
    """
    audit_repr_field = None

    def _object_repr(self, instance):
        if self.audit_repr_field:
            return str(getattr(instance, self.audit_repr_field, '') or '')
        return str(instance)

    def perform_create(self, serializer):
        with transaction.atomic():
            instance = serializer.save()
            write_audit(
                actor=self.request.user,
                action='CREATE',
                model_name=instance.__class__.__name__,
                object_id=instance.pk,
                object_repr=self._object_repr(instance),
                after=serializer.data,
            )

    def perform_update(self, serializer):
        with transaction.atomic():
            before = self.get_serializer(serializer.instance).data
            instance = serializer.save()
            write_audit(
                actor=self.request.user,
                action='UPDATE',
                model_name=instance.__class__.__name__,
                object_id=instance.pk,
                object_repr=self._object_repr(instance),
                before=before,
                after=serializer.data,
            )

    def perform_destroy(self, instance):
        with transaction.atomic():
            model_name = instance.__class__.__name__
            object_id = instance.pk
            object_repr = self._object_repr(instance)
            before = self.get_serializer(instance).data
            instance.delete()
            write_audit(
                actor=self.request.user,
                action='DELETE',
                model_name=model_name,
                object_id=object_id,
                object_repr=object_repr,
                before=before,
            )
