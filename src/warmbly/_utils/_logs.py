"""Logging helpers with secret redaction.

The SDK logs through a single ``warmbly`` logger and attaches a
:class:`logging.NullHandler` so that, by default, libraries stay silent and the
application controls handlers/levels (the standard-library guidance). Nothing
here calls :func:`logging.basicConfig` or sets a level.

:func:`redact` scrubs credentials before any value reaches a log record.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping

__all__ = ["logger", "redact", "redact_headers"]

logger = logging.getLogger("warmbly")
logger.addHandler(logging.NullHandler())

# Header names whose values must never be logged (compared case-insensitively).
_SENSITIVE_HEADERS = frozenset(
    {
        "authorization",
        "proxy-authorization",
        "x-api-key",
        "api-key",
        "x-warmbly-signature",
        "cookie",
        "set-cookie",
    }
)

# Body/query field names whose values must never be logged.
_SENSITIVE_FIELDS = frozenset(
    {
        "client_secret",
        "code",
        "code_verifier",
        "refresh_token",
        "access_token",
        "secret",
        "password",
        "token",
    }
)

# Any value that looks like a prefixed Warmbly credential.
_TOKEN_RE = re.compile(r"\bwm(?:bly|at|rt|ac|cid|cs)_[A-Za-z0-9_\-]+")

_REDACTED = "[redacted]"


def _scrub_text(value: str) -> str:
    return _TOKEN_RE.sub(_REDACTED, value)


def redact(value: object) -> object:
    """Return a copy of *value* with secrets replaced by ``[redacted]``.

    Recurses through mappings and sequences, redacting both sensitive field
    names and any string that matches a Warmbly token prefix.
    """
    if isinstance(value, str):
        return _scrub_text(value)
    if isinstance(value, Mapping):
        return {
            key: (
                _REDACTED
                if isinstance(key, str) and key.lower() in _SENSITIVE_FIELDS
                else redact(val)
            )
            for key, val in value.items()
        }
    if isinstance(value, (list, tuple)):
        scrubbed = [redact(item) for item in value]
        return type(value)(scrubbed) if isinstance(value, tuple) else scrubbed
    return value


def redact_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Return *headers* with sensitive values replaced by ``[redacted]``."""
    return {
        key: (_REDACTED if key.lower() in _SENSITIVE_HEADERS else _scrub_text(val))
        for key, val in headers.items()
    }
