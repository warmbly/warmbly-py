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

## Webhooks

::: warmbly.resources.webhooks.Webhooks

## Analytics

::: warmbly.resources.analytics.Analytics

## Integrations

::: warmbly.resources.integrations.Integrations

## Templates

::: warmbly.resources.templates.Templates

## CRM

::: warmbly.resources.crm.Crm

## Teams

::: warmbly.resources.teams.Teams

## Plans

::: warmbly.resources.plans.Plans

## Timezones

::: warmbly.resources.timezones.Timezones

## Unibox

::: warmbly.resources.unibox.Unibox
