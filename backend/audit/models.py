from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Append-only record of security-sensitive and business-significant
    actions. Never edited or deleted through the normal API - see
    audit/views.py (read-only ListAPIView) and audit/admin.py (add/change/
    delete permissions all disabled). Rows are written by
    audit.services.write_audit(), called from inside the same
    transaction.atomic() block as the action it records, so a rolled-back
    business operation rolls back its audit entry too.

    Never store: passwords, password hashes, JWT access/refresh tokens,
    SECRET_KEY, database credentials, or API keys in any field below.
    """

    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('CONFIRM', 'Confirm'),
        ('CANCEL', 'Cancel'),
        ('ACTIVATE', 'Activate'),
        ('DEACTIVATE', 'Deactivate'),
        ('ROLE_CHANGE', 'Role Change'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('STATUS_CHANGE', 'Status Change'),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_logs',
    )
    # Denormalized snapshot so the log stays readable even if the actor
    # account is later renamed or removed.
    actor_username = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp', '-id']
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.action} {self.model_name}({self.object_id}) by {self.actor_username or 'system'}"
