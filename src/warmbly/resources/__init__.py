"""Typed resource groups exposed on the :class:`~warmbly.Warmbly` client."""

from __future__ import annotations

from .advisor import Advisor, AsyncAdvisor
from .ai_skills import AISkills, AsyncAISkills
from .ai_tools import AITools, AsyncAITools
from .analytics import Analytics, AsyncAnalytics
from .api_keys import ApiKeys, AsyncApiKeys
from .audit_logs import AsyncAuditLogs, AuditLogs
from .automations import AsyncAutomations, Automations
from .campaigns import AsyncCampaigns, Campaigns
from .contacts import AsyncContacts, Contacts
from .crm import AsyncCrm, Crm
from .deliverability import AsyncDeliverability, Deliverability
from .emails import AsyncEmails, Emails
from .forms import AsyncForms, Forms
from .generation import AsyncGeneration, Generation
from .groups import (
    AsyncCategories,
    AsyncFolders,
    AsyncGroups,
    AsyncTags,
    Categories,
    Folders,
    Groups,
    Tags,
)
from .identity import AsyncMe, Me
from .integrations import AsyncIntegrations, Integrations
from .lead_sync import AsyncLeadSync, LeadSync
from .meetings import AsyncMeetings, Meetings
from .oauth_applications import AsyncOAuthApplications, OAuthApplications
from .outreach import AsyncOutreach, Outreach
from .plans import AsyncPlans, Plans
from .segments import AsyncSegments, Segments
from .suppressions import AsyncSuppressions, Suppressions
from .tasks import AsyncTasks, Tasks
from .teams import AsyncTeams, Teams
from .templates import AsyncTemplates, Templates
from .timezones import AsyncTimezones, Timezones
from .unibox import AsyncUnibox, Unibox
from .warmup_routing import AsyncWarmupRouting, WarmupRouting
from .webhooks import (
    AsyncWebhooks,
    Webhooks,
    verify_signature,
    verify_webhook_signature,
)

__all__ = [
    "AISkills",
    "AITools",
    "Advisor",
    "Analytics",
    "ApiKeys",
    "AsyncAISkills",
    "AsyncAITools",
    "AsyncAdvisor",
    "AsyncAnalytics",
    "AsyncApiKeys",
    "AsyncAuditLogs",
    "AsyncAutomations",
    "AsyncCampaigns",
    "AsyncCategories",
    "AsyncContacts",
    "AsyncCrm",
    "AsyncDeliverability",
    "AsyncEmails",
    "AsyncFolders",
    "AsyncForms",
    "AsyncGeneration",
    "AsyncGroups",
    "AsyncIntegrations",
    "AsyncLeadSync",
    "AsyncMe",
    "AsyncMeetings",
    "AsyncOAuthApplications",
    "AsyncOutreach",
    "AsyncPlans",
    "AsyncSegments",
    "AsyncSuppressions",
    "AsyncTags",
    "AsyncTasks",
    "AsyncTeams",
    "AsyncTemplates",
    "AsyncTimezones",
    "AsyncUnibox",
    "AsyncWarmupRouting",
    "AsyncWebhooks",
    "AuditLogs",
    "Automations",
    "Campaigns",
    "Categories",
    "Contacts",
    "Crm",
    "Deliverability",
    "Emails",
    "Folders",
    "Forms",
    "Generation",
    "Groups",
    "Integrations",
    "LeadSync",
    "Me",
    "Meetings",
    "OAuthApplications",
    "Outreach",
    "Plans",
    "Segments",
    "Suppressions",
    "Tags",
    "Tasks",
    "Teams",
    "Templates",
    "Timezones",
    "Unibox",
    "WarmupRouting",
    "Webhooks",
    "verify_signature",
    "verify_webhook_signature",
]
