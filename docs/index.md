# warmbly-py

The official Python SDK for the [Warmbly](https://warmbly.com) API — REST
resources, OAuth2, and a realtime gateway, with first-class **sync** and
**async** support.

```python
import os
from warmbly import Warmbly

client = Warmbly(api_key=os.environ["WARMBLY_API_KEY"])

campaign = client.campaigns.create(name="Q3 outreach")
print(campaign.id)
```

That is the whole story: one client object owns your configuration and a shared
connection pool, and every API resource group hangs off it as an attribute
(`client.campaigns`, `client.api_keys`, `client.contacts`, …). Swap `Warmbly`
for `AsyncWarmbly`, add `await`, and the same code runs on asyncio.

## Three ways to authenticate

Every auth mode resolves to a bearer token on the wire. Pick whichever fits how
your code runs.

| Mode | How | When |
|---|---|---|
| **API key** | `Warmbly(api_key="wmbly_...")` or set `WARMBLY_API_KEY` | Server-side scripts and backends you control. |
| **OAuth2 access token** | `Warmbly(api_key="wmat_...")` | You already hold a user's access token (any bearer token works). |
| **OAuth2 flow** | `from warmbly.oauth import OAuth2Client` | Apps that act on behalf of other users — PKCE, refresh, and storage are handled for you. |

See the [Authentication guide](guides/auth.md) for the full picture and the
[OAuth2 guide](guides/oauth.md) for the interactive flow.

## Feature highlights

- **Sync and async, same API.** Every method on `Warmbly` has an `await`-able
  twin on [`AsyncWarmbly`](reference/client.md) — no second mental model.
- **OAuth2 done right.** [`warmbly.oauth`](reference/oauth.md) ships PKCE,
  authorization-code and client-credentials grants, token refresh, revocation,
  and pluggable storage (memory, encrypted file, OS keyring).
- **Realtime gateway.** [`AsyncGatewayClient`](reference/gateway.md) subscribes
  to live events over a single resilient WebSocket, with heartbeats, automatic
  reconnect, and session resume handled for you (a blocking `GatewayClient`
  wrapper is included too).
- **Webhook verification.** [`verify_webhook_signature`](guides/webhooks.md)
  validates inbound payloads before you trust them.
- **Typed models.** Responses are Pydantic models with editor autocompletion;
  unknown fields are preserved for forward compatibility, and every response
  carries a `.request_id`.
- **Retries and pagination, built in.** Transient failures (408/409/429/5xx)
  are [retried](guides/retries.md) with backoff and jitter, write requests get
  automatic idempotency keys, and list endpoints
  [auto-paginate](guides/pagination.md) as you iterate.

## Get started

- [Install](getting-started/install.md) — `pip install warmbly`, the `[oauth]`
  extra, and verifying your setup.
- [Quickstart](getting-started/quickstart.md) — a 60-second tour of the client.

## Guides

- [Authentication](guides/auth.md) and [OAuth2](guides/oauth.md)
- [Async](guides/async.md)
- [Pagination](guides/pagination.md)
- [Errors](guides/errors.md) and [Retries](guides/retries.md)
- [Realtime gateway](guides/realtime.md)
- [Webhooks](guides/webhooks.md)

## API reference

- [Client](reference/client.md)
- [Resources](reference/resources.md)
- [Gateway](reference/gateway.md)
- [OAuth](reference/oauth.md)
- [Exceptions](reference/exceptions.md)
