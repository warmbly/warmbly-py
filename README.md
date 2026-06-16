# warmbly-py

The official Python SDK for the [Warmbly](https://warmbly.com) API — REST resources, OAuth2, and a realtime gateway, with first-class sync **and** async support.

[![PyPI version](https://img.shields.io/pypi/v/warmbly.svg)](https://pypi.org/project/warmbly/)
[![Python versions](https://img.shields.io/pypi/pyversions/warmbly.svg)](https://pypi.org/project/warmbly/)
[![Downloads](https://static.pepy.tech/badge/warmbly/month)](https://pepy.tech/project/warmbly)
[![CI](https://img.shields.io/github/actions/workflow/status/warmbly/warmbly-py/ci.yml?branch=main&logo=github&label=CI)](https://github.com/warmbly/warmbly-py/actions?query=branch%3Amain)
[![License](https://img.shields.io/pypi/l/warmbly.svg)](https://github.com/warmbly/warmbly-py/blob/main/LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Docs](https://img.shields.io/readthedocs/warmbly-py)](https://warmbly-py.readthedocs.io)

---

## Installation

```bash
pip install warmbly
```

Interactive OAuth2 flows and secure token storage are an optional extra:

```bash
pip install "warmbly[oauth]"
```

Requires Python 3.10+.

## Quickstart

```python
import os
from warmbly import Warmbly

client = Warmbly(api_key=os.environ["WARMBLY_API_KEY"])

campaign = client.campaigns.create(name="Q3 outreach")
print(campaign.id)

for key in client.api_keys.list():
    print(key.name, key.status)
```

The client reads `WARMBLY_API_KEY` from the environment automatically, so you
can also just write `client = Warmbly()`.

### Async

Every method has an `await`-able twin on `AsyncWarmbly` — swap the class, add
`await`, and iterate with `async for`:

```python
import asyncio
import os
from warmbly import AsyncWarmbly


async def main() -> None:
    client = AsyncWarmbly(api_key=os.environ["WARMBLY_API_KEY"])
    campaign = await client.campaigns.create(name="Q3 outreach")
    print(campaign.id)

    async for key in client.api_keys.list():
        print(key.name)

    await client.close()


asyncio.run(main())
```

## Authentication

The SDK supports all three Warmbly auth modes; each is sent as a bearer token.

| Mode | How |
|---|---|
| **API key** | `Warmbly(api_key="wmbly_...")` or `WARMBLY_API_KEY` env var |
| **OAuth2 access token** | `Warmbly(api_key="wmat_...")` (any bearer token works) |
| **OAuth2 flow** | `from warmbly.oauth import OAuth2Client` — see the [OAuth guide](https://warmbly-py.readthedocs.io/guides/oauth) |

### OAuth2 in three lines

```python
from warmbly.oauth import OAuth2Client

oauth = OAuth2Client(client_id="wmcid_...", client_secret="wmcs_...",
                     redirect_uri="https://app.example.com/callback")

# 1. Send the user to authorize (PKCE handled for you):
url, state, verifier = oauth.authorization_url(scopes=["read_campaigns", "send_campaigns"])

# 2. Exchange the code returned to your redirect URI:
token = oauth.exchange_code(code, state=state, expected_state=state, code_verifier=verifier)

# 3. Use the access token:
client = Warmbly(api_key=token.access_token)
```

You can also register and manage OAuth2 applications programmatically via
`client.oauth_applications.create(...)`.

## Realtime gateway

Subscribe to live events over a single resilient WebSocket connection
(heartbeats, automatic reconnect, and session resume are handled for you):

```python
import asyncio
from warmbly import AsyncGatewayClient


async def main() -> None:
    gateway = AsyncGatewayClient(token="wmbly_...")  # needs the realtime_subscribe scope

    @gateway.on_event("CAMPAIGN_STARTED")
    async def handle(payload: dict) -> None:
        print("campaign started:", payload["campaign_id"])

    await gateway.connect()
    await gateway.subscribe("org:00000000-0000-0000-0000-000000000000")
    await gateway.run_forever()


asyncio.run(main())
```

## Pagination

List endpoints return an iterator that transparently fetches every page:

```python
for contact in client.contacts.list():   # walks all pages
    print(contact.email)

page = client.api_keys.list()             # or work a page at a time
print(page.data, page.has_more, page.next_cursor)
```

## Error handling

Every error inherits from `warmbly.WarmblyError`. HTTP failures map to a
status-specific subclass carrying `.status_code`, `.request_id`, and the parsed
`.body`.

| Status | Exception |
|---|---|
| 400 | `BadRequestError` |
| 401 | `AuthenticationError` |
| 403 | `PermissionDeniedError` |
| 404 | `NotFoundError` |
| 409 | `ConflictError` |
| 422 | `UnprocessableEntityError` |
| 429 | `RateLimitError` (`.retry_after`) |
| 5xx | `InternalServerError` |
| network / timeout | `APIConnectionError` / `APITimeoutError` |
| OAuth token endpoint | `OAuthError` (`.error`, `.error_description`) |

```python
from warmbly import Warmbly, RateLimitError, NotFoundError

client = Warmbly()
try:
    client.campaigns.retrieve("missing")
except NotFoundError:
    ...
except RateLimitError as err:
    print(f"retry after {err.retry_after}s (request {err.request_id})")
```

## Configuration

```python
client = Warmbly(
    api_key="wmbly_...",
    base_url="https://api.warmbly.com/v1",  # or WARMBLY_BASE_URL
    timeout=30.0,                            # seconds, or an httpx.Timeout
    max_retries=2,                           # 408/409/429/5xx with backoff + jitter
)
```

Idempotency keys are added automatically to write requests so retries are safe;
pass `idempotency_key=...` to a method to supply your own.

## Webhooks

Verify inbound webhook signatures before trusting a payload:

```python
from warmbly import verify_webhook_signature

event = verify_webhook_signature(
    payload=request.body,
    signature=request.headers["X-Warmbly-Signature"],
    secret=endpoint_secret,
)
```

## Documentation

Full documentation, guides, and the API reference live at
**[warmbly-py.readthedocs.io](https://warmbly-py.readthedocs.io)**.

## Contributing

Contributions are welcome! Please read
[CONTRIBUTING.md](./.github/CONTRIBUTING.md) and our
[Code of Conduct](./.github/CODE_OF_CONDUCT.md) to get started.

## License

[MIT](./LICENSE) © Warmbly
