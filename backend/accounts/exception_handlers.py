import logging
from rest_framework.views import exception_handler
from rest_framework.exceptions import PermissionDenied, NotAuthenticated, AuthenticationFailed

logger = logging.getLogger(__name__)


def logging_exception_handler(exc, context):
    """Wraps DRF's default exception handler purely for observability - it
    never changes the response DRF would already return, only adds a log
    line for security-relevant failures (403/401). Logs the username (or
    'anonymous'), the request path, and the exception type - never a
    token, password, or other credential.
    """
    response = exception_handler(exc, context)

    if isinstance(exc, (PermissionDenied, NotAuthenticated, AuthenticationFailed)):
        request = context.get('request')
        user = getattr(request, 'user', None)
        username = getattr(user, 'username', None) if user and getattr(user, 'is_authenticated', False) else 'anonymous'
        path = getattr(request, 'path', '<unknown>')
        logger.warning(
            "Access denied: user=%s path=%s exception=%s",
            username, path, exc.__class__.__name__,
        )

    return response
