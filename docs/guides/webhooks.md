# Webhooks

Webhooks deliver Warmbly events to your server as signed HTTP POST requests. Use
them when you'd rather receive events at an HTTPS endpoint than hold a connection
open with the [realtime gateway](realtime.md).

There are two halves to working with webhooks:

1. **Verifying inbound deliveries** so you can trust a payload before acting on
   it, with the `verify_webhook_signature`
   helper.
2. **Managing endpoints** (registering, listing, updating, and inspecting them)
   via `client.webhooks`.

## Verifying inbound signatures

Every outbound webhook request carries three headers:

| Header | What it is |
| --- | --- |
| `X-Warmbly-Event` | The event type, so you can route without parsing the body. |
| `X-Warmbly-Event-Id` | The event id. Stable across retries, so use it to dedupe. |
| `X-Warmbly-Signature` | `t=<unix>,v1=<hex>` — see below. |

The signature is HMAC-SHA256 over `"{t}.{raw_body}"` using your endpoint's
signing secret, in the same shape Stripe uses. Folding the timestamp into the
digest is what makes a captured request un-replayable: it cannot be re-stamped
without the secret.

`verify_webhook_signature` recomputes the digest, compares it against the
header's `v1` value in constant time, rejects a timestamp outside the tolerance
window, and (on success) returns the parsed JSON body as a `dict`. Any failure
raises [`WarmblyError`][warmbly.WarmblyError].

```python
from warmbly import verify_webhook_signature, WarmblyError

event = verify_webhook_signature(
    payload=request.body,                            # raw bytes or str, NOT re-serialized
    signature=request.headers["X-Warmbly-Signature"],
    secret=endpoint_secret,
)
print(event["event_type"], event["id"])
```

!!! warning "Pass the raw body"
    Verify against the **exact bytes** you received. If you parse the JSON and
    re-serialize it before verifying, whitespace and key ordering will differ and
    the signature will not match. Read the raw body first, verify, then use the
    `dict` that `verify_webhook_signature` returns.

Pass the header value verbatim; the helper parses it. During a secret rotation
the server may send more than one `v1` digest, and any match is accepted.

### Replay tolerance

By default a signature more than 300 seconds old is rejected, which bounds how
long a captured request stays usable. Widen it if your queue can lag, or pass
`tolerance=None` to skip the check entirely — for instance when verifying a
delivery you recorded earlier.

```python
verify_webhook_signature(
    payload=body,
    signature=signature_header,
    secret=endpoint_secret,
    tolerance=900,  # accept up to 15 minutes of clock skew / queue lag
)
```

It's available as a top-level import (no client instance needed):

```python
from warmbly import verify_webhook_signature
# verify_signature is an alias for the same function
from warmbly import verify_signature
```

### Example: Flask

```python
from flask import Flask, request, abort
from warmbly import verify_webhook_signature, WarmblyError

app = Flask(__name__)
ENDPOINT_SECRET = "whsec_..."  # from the create / rotate-secret response


@app.post("/warmbly/webhook")
def webhook():
    try:
        event = verify_webhook_signature(
            payload=request.get_data(),  # raw body bytes
            signature=request.headers.get("X-Warmbly-Signature", ""),
            secret=ENDPOINT_SECRET,
        )
    except WarmblyError:
        abort(400, "invalid signature")

    # Trusted: dispatch on the event type.
    if event["event_type"] == "campaign.reply_received":
        ...

    return "", 204
```

### Example: FastAPI

```python
from fastapi import FastAPI, Request, HTTPException
from warmbly import verify_webhook_signature, WarmblyError

app = FastAPI()
ENDPOINT_SECRET = "whsec_..."


@app.post("/warmbly/webhook")
async def webhook(request: Request):
    body = await request.body()  # raw bytes
    try:
        event = verify_webhook_signature(
            payload=body,
            signature=request.headers.get("X-Warmbly-Signature", ""),
            secret=ENDPOINT_SECRET,
        )
    except WarmblyError:
        raise HTTPException(status_code=400, detail="invalid signature")

    return {"received": event["event_type"]}
```

## Managing endpoints

The `client.webhooks` resource registers and inspects endpoints. It works the
same on `Warmbly` and `AsyncWarmbly` (add `await` for the async client).

### Register an endpoint

`create()` returns a `WebhookEndpoint`. The plaintext signing **`secret` is
returned only here (and on rotate-secret)**. Store it immediately, because it
can't be retrieved again.

```python
endpoint = client.webhooks.create(
    url="https://app.example.com/warmbly/webhook",
    event_types=["campaign.reply_received", "campaign.completed"],
    description="Prod reply handler",
)

print(endpoint.id)
secret = endpoint.secret  # save this securely; shown only once
```

To discover which event types you can subscribe to, list them. `firehose` marks
the high-volume ones, which are opt-in for a reason:

```python
for et in client.webhooks.event_types():
    print(et.type, et.category, "-", et.description, "firehose" if et.firehose else "")
```

### List endpoints

`list()` returns an auto-paginating cursor page: iterate it directly to walk
every page:

```python
for endpoint in client.webhooks.list():
    print(endpoint.id, endpoint.url, endpoint.enabled)
```

### Update an endpoint

Change the URL, the subscribed event types, the description, or toggle the
endpoint on/off. Only the fields you pass are modified.

```python
client.webhooks.update(
    endpoint.id,
    event_types=["campaign.reply_received"],
    enabled=False,  # pause deliveries without deleting the endpoint
)
```

### Update an endpoint's URL

Changing the URL clears verification: Warmbly re-challenges the new address and
holds deliveries until it echoes the challenge, so a mistyped host cannot
silently swallow your events.

### Rotate the signing secret

`rotate_secret()` issues a new secret and returns it on the result (again, only
this once). Roll your verifier over to the new value:

```python
rotated = client.webhooks.rotate_secret(endpoint.id)
new_secret = rotated.secret
```

### Verify an endpoint

`verify()` asks Warmbly to deliver a signed challenge. The call returns as soon
as the challenge is queued; the endpoint flips to verified once it echoes the
`challenge` value from the body, either back in its response body or in the
`X-Warmbly-Webhook-Challenge` header.

```python
result = client.webhooks.verify(endpoint.id)
print(result.status)  # "challenge_sent"
```

### Delete an endpoint

```python
client.webhooks.delete(endpoint.id)
```

## Inspecting deliveries

Each attempt to deliver an event to an endpoint is recorded as a
`WebhookDelivery` with a `status` of `pending`, `in_flight`, `delivered`,
`failed`, or `abandoned`.

List deliveries across all endpoints, or scope to one endpoint:

```python
# Across every endpoint.
for delivery in client.webhooks.deliveries():
    print(delivery.event_type, delivery.status, delivery.response_status)

# For a single endpoint, narrowed to the failures.
for delivery in client.webhooks.endpoint_deliveries(endpoint.id, status="failed"):
    print(delivery.id, delivery.error_reason, delivery.response_body_excerpt)
```

Re-attempt a delivery that previously failed:

```python
client.webhooks.redeliver(delivery.id)
```

Events the dispatch throttle dropped are recorded separately, rolled up by day
over the last 30 days:

```python
for drop in client.webhooks.throttle_drops():
    print(drop.day, drop.event_type, drop.dropped_windows, drop.last_dropped_at)
```

## Async usage

Everything above has an `await`-able twin on `AsyncWarmbly`. List methods return
async cursor pages, so iterate them with `async for`:

```python
import asyncio
from warmbly import AsyncWarmbly


async def main() -> None:
    client = AsyncWarmbly()

    endpoint = await client.webhooks.create(
        url="https://app.example.com/warmbly/webhook",
        event_types=["campaign.completed"],
    )
    print(endpoint.id)
    await store_secret(endpoint.secret)  # shown once; store it, never log it

    async for delivery in client.webhooks.endpoint_deliveries(endpoint.id):
        print(delivery.status)

    await client.close()


asyncio.run(main())
```

Note that `verify_webhook_signature` is a synchronous, pure-computation helper.
There's no async variant, because verifying a signature does no I/O. Call it the
same way regardless of which client you use.

## See also

- [Realtime gateway](realtime.md): for a persistent WebSocket stream of events
  instead of HTTP callbacks.
- [Pagination](pagination.md): how the cursor pages returned by the list
  methods work.
