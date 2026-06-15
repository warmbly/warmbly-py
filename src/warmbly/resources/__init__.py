"""Typed resource groups exposed on the :class:`~warmbly.Warmbly` client."""

from __future__ import annotations

from .api_keys import ApiKeys, AsyncApiKeys
from .oauth_applications import AsyncOAuthApplications, OAuthApplications

__all__ = [
    "ApiKeys",
    "AsyncApiKeys",
    "OAuthApplications",
    "AsyncOAuthApplications",
]
