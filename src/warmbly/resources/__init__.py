"""Typed resource groups exposed on the :class:`~warmbly.Warmbly` client."""

from __future__ import annotations

from .analytics import Analytics, AsyncAnalytics
from .api_keys import ApiKeys, AsyncApiKeys
from .campaigns import AsyncCampaigns, Campaigns
from .contacts import AsyncContacts, Contacts
from .crm import AsyncCrm, Crm
from .emails import AsyncEmails, Emails
from .integrations import AsyncIntegrations, Integrations
from .oauth_applications import AsyncOAuthApplications, OAuthApplications
from .plans import AsyncPlans, Plans
from .teams import AsyncTeams, Teams
from .templates import AsyncTemplates, Templates
from .timezones import AsyncTimezones, Timezones
from .unibox import AsyncUnibox, Unibox
from .webhooks import (
    AsyncWebhooks,
    Webhooks,
    verify_signature,
    verify_webhook_signature,
)

__all__ = [
    "Analytics",
    "ApiKeys",
    "AsyncAnalytics",
    "AsyncApiKeys",
    "AsyncCampaigns",
    "AsyncContacts",
    "AsyncCrm",
    "AsyncEmails",
    "AsyncIntegrations",
    "AsyncOAuthApplications",
    "AsyncPlans",
    "AsyncTeams",
    "AsyncTemplates",
    "AsyncTimezones",
    "AsyncUnibox",
    "AsyncWebhooks",
    "Campaigns",
    "Contacts",
    "Crm",
    "Emails",
    "Integrations",
    "OAuthApplications",
    "Plans",
    "Teams",
    "Templates",
    "Timezones",
    "Unibox",
    "Webhooks",
    "verify_signature",
    "verify_webhook_signature",
]
