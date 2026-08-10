from audit.models import AuditLog


def write_audit(actor, action, model_name, object_id='', object_repr='', before=None, after=None, metadata=None):
    """Writes one AuditLog row. Call from inside the same transaction.atomic()
    block as the business operation it records, so a rollback of that
    operation rolls back the audit entry with it.

    Never pass password/hash/JWT/refresh-token/SECRET_KEY/DB-credential
    values in before/after/metadata - only safe, non-sensitive fields.
    """
    AuditLog.objects.create(
        actor=actor if getattr(actor, 'is_authenticated', False) else None,
        actor_username=getattr(actor, 'username', '') or '',
        action=action,
        model_name=model_name,
        object_id=str(object_id) if object_id != '' else '',
        object_repr=object_repr,
        before_state=before,
        after_state=after,
        metadata=metadata,
    )
