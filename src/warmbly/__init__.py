"""warmbly — the official Python SDK for the Warmbly API.

Exposes synchronous and asynchronous clients, the shared response
:class:`BaseModel`, the exception hierarchy, scope helpers, and the realtime
gateway. Everything not listed in ``__all__`` (modules prefixed with ``_``) is
private and may change without notice.
"""

from __future__ import annotations

from ._client import AsyncWarmbly, Warmbly
from ._exceptions import (
    APIConnectionError,
    APIError,
    APIResponseValidationError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    GatewayError,
    InternalServerError,
    NotFoundError,
    OAuthError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
    WarmblyError,
)
from ._models import BaseModel
from ._types import NOT_GIVEN, NotGiven, Omit, RequestOptions, Timeout
from ._utils import mask_to_scopes, scopes_to_mask

try:
    from ._version import __version__
except ImportError:  # pragma: no cover - source checkout without a build
    try:
        from importlib.metadata import version as _v

        __version__ = _v("warmbly")
    except Exception:  # noqa: BLE001
        __version__ = "0.0.0+dev"

__all__ = [
    "__version__",
    # Clients
    "Warmbly",
    "AsyncWarmbly",
    # Models / types
    "BaseModel",
    "NOT_GIVEN",
    "NotGiven",
    "Omit",
    "RequestOptions",
    "Timeout",
    # Scope helpers
    "scopes_to_mask",
    "mask_to_scopes",
    # Exceptions
    "WarmblyError",
    "APIError",
    "APIConnectionError",
    "APITimeoutError",
    "APIResponseValidationError",
    "APIStatusError",
    "BadRequestError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "RateLimitError",
    "InternalServerError",
    "OAuthError",
    "GatewayError",
]
