"""
Custom DRF exception handler — converts Django's native ValidationError to a
proper DRF 400 response so model-level `clean()` errors are returned as JSON
rather than bubbling up as 500s.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    # Convert Django model ValidationError → DRF ValidationError (400)
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            detail = exc.message_dict
        elif hasattr(exc, "messages"):
            detail = exc.messages
        else:
            detail = str(exc)
        exc = DRFValidationError(detail=detail)

    return drf_exception_handler(exc, context)
