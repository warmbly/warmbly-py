# Resources

Each resource group is reachable as an attribute on the client, for example
`client.campaigns` or `client.api_keys`. Every group provides the standard
`create`/`list`/`retrieve`/`update`/`delete` operations where the underlying
endpoint supports them, plus resource-specific actions. List operations return a
`SyncCursorPage` you can iterate directly with `for`.

```python
from warmbly import Warmbly

client = Warmbly(api_key="wmbly_...")
for campaign in client.campaigns.list():
    print(campaign.id)
```

!!! note "Async mirrors"
    Only the synchronous resource classes are documented below. Each one has an
    `Async*` counterpart (`AsyncApiKeys`, `AsyncCampaigns`, …) with an identical
    method surface returning awaitables; list operations on the async clients
    return an `AsyncCursorPage` you iterate with `async for`.

!!! info "What is not here"
    The clients cover what an API key or OAuth token can reach. Routes that
    require a browser session — organization governance, billing and
    subscriptions, mailbox onboarding, and the OAuth consent flow — are
    deliberately absent, because a long-lived credential cannot call them.

## Identity

::: warmbly.resources.identity.Me

## API keys

::: warmbly.resources.api_keys.ApiKeys

## OAuth applications

::: warmbly.resources.oauth_applications.OAuthApplications

## Campaigns

::: warmbly.resources.campaigns.Campaigns

## Emails

::: warmbly.resources.emails.Emails

## Contacts

::: warmbly.resources.contacts.Contacts

## Unibox

::: warmbly.resources.unibox.Unibox

## Webhooks

::: warmbly.resources.webhooks.Webhooks

## Analytics

::: warmbly.resources.analytics.Analytics

## Advisor

::: warmbly.resources.advisor.Advisor

## Integrations

::: warmbly.resources.integrations.Integrations

## Automations

::: warmbly.resources.automations.Automations

## Lead sync

::: warmbly.resources.lead_sync.LeadSync

## Templates

::: warmbly.resources.templates.Templates

## CRM

::: warmbly.resources.crm.Crm

## Meetings

::: warmbly.resources.meetings.Meetings

## Teams

::: warmbly.resources.teams.Teams

## Folders, tags, and categories

`client.folders`, `client.tags`, and `client.categories` are the same resource
bound to three route prefixes.

::: warmbly.resources.groups.Groups

## AI generation

::: warmbly.resources.generation.Generation

## AI skills

::: warmbly.resources.ai_skills.AISkills

## Outreach settings

::: warmbly.resources.outreach.Outreach

## Deliverability

::: warmbly.resources.deliverability.Deliverability

## Warmup routing

::: warmbly.resources.warmup_routing.WarmupRouting

## Task dead-letter queue

::: warmbly.resources.tasks.Tasks

## Audit logs

::: warmbly.resources.audit_logs.AuditLogs

## Plans

::: warmbly.resources.plans.Plans

## Timezones

::: warmbly.resources.timezones.Timezones
