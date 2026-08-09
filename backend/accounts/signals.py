import logging
from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request=None, **kwargs):
    """Django's authenticate() already strips 'password' out of the
    credentials dict before sending this signal, but we're deliberately
    defensive anyway and only ever read the 'username' key - nothing else
    in `credentials` is touched or logged.
    """
    username = credentials.get('username', '<unknown>')
    ip = request.META.get('REMOTE_ADDR', '<unknown>') if request is not None else '<unknown>'
    logger.warning("Failed login attempt: username=%s ip=%s", username, ip)
