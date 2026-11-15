# Gateway

The realtime gateway is a WebSocket client for Warmbly's event stream (campaign,
email, contact, account, and bulk-operation events) with topic presence and
sequence-based resume across reconnects.

Two clients with identical surfaces are provided:

* [`AsyncGatewayClient`][warmbly.AsyncGatewayClient]: the native `asyncio`
  client.
* [`GatewayClient`][warmbly.GatewayClient]: a blocking facade that runs the
  async client on a background event loop, for use from synchronous code.

Event names are available as constants on
[`GatewayEvent`][warmbly.gateway.GatewayEvent].

```python
from warmbly.gateway import AsyncGatewayClient, GatewayEvent

gw = AsyncGatewayClient(token="wmbly_...")

@gw.on_event(GatewayEvent.CAMPAIGN_STARTED)
async def handle(topic, payload):
    print(payload["campaign_id"])

await gw.connect()
await gw.subscribe("org:org_123", intents=["CAMPAIGN"])
await gw.run_forever()
```

New event families are exposed as constants too, for example
`GatewayEvent.PLACEMENT_TEST_UPDATED`, `MAILBOX_IMPORT_PROGRESS`,
`CONTACT_IMPORT_PROGRESS`, `CRM_SYNCED`, `WARMUP_PLACEMENT` and
`WARMUP_ACTIVITY`. Unknown event names are still delivered to `on_event`
handlers. `EVENT_PERMISSIONS` maps an event to the workspace permission the
server requires, and `intent_matches(event_type, intents)` mirrors the server's
intent filter.

## AsyncGatewayClient

::: warmbly.AsyncGatewayClient

## GatewayClient

::: warmbly.GatewayClient

## GatewayEvent

::: warmbly.gateway.GatewayEvent
