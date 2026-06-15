# Retries & timeouts

The client automatically retries transient failures with exponential backoff
and jitter. By default it makes up to **2** retries (3 total attempts) per
request. You can tune or disable this globally or per request.

## What gets retried

A request is retried when **both** of the following hold:

1. **The method is safe to retry.** `GET`, `HEAD`, `OPTIONS`, `PUT`, and
   `DELETE` are always considered retry-safe. `POST` is retried **only** when it
   carries an `Idempotency-Key` — which the SDK adds automatically for you (see
   [Idempotency keys](#idempotency-keys) below), so writes are safely retried in
   practice.
2. **The failure looks transient**, i.e. one of:
    - a connection error that never reached the server, or a timeout;
    - an HTTP status of **408**, **409**, **429**, or any **5xx** (`>= 500`).

Anything else — `400`, `401`, `403`, `404`, `422`, and other 4xx — is **not**
retried and surfaces immediately as the corresponding
[exception](errors.md).

| Trigger | Retried? |
| ------- | -------- |
| Connection error (couldn't reach server) | Yes |
| Timeout | Yes |
| `408 Request Timeout` | Yes |
| `409 Conflict` | Yes |
| `429 Too Many Requests` | Yes (honors `Retry-After`) |
| `5xx` server errors | Yes |
| `400` / `401` / `403` / `404` / `422` | No |
| Successful `2xx` | No |

!!! note "POST without an idempotency key is not retried"
    Retrying a non-idempotent write could duplicate side effects. Since the SDK
    auto-attaches an `Idempotency-Key` to every JSON `POST`, your `create(...)`
    calls are retry-eligible by default. (Form-encoded POSTs — used internally
    by the OAuth token endpoint — do not get an idempotency key and are not
    retried.)

## Backoff and jitter

Between attempts the client sleeps for an exponentially growing delay with
randomized jitter, so concurrent clients don't retry in lockstep:

- Base delay: `min(0.5 * 2 ** attempt, 8.0)` seconds — i.e. it doubles each
  attempt, starting at **0.5 s**, capped at **8 s**.
- Jitter: the base delay is multiplied by a random factor between **0.75** and
  **1.0**.

So the first retry waits roughly 0.75–1.0 s, the second roughly 1.5–2.0 s, and
so on, never exceeding ~8 s.

### `Retry-After` takes priority

For responses that carry a `Retry-After` header (typically on `429`), the SDK
uses the server's value instead of the computed backoff — as long as it's a
positive duration no greater than **60 s**. Values outside that window fall back
to the normal backoff schedule. Both numeric-seconds and HTTP-date forms of
`Retry-After` are understood.

## Configuring `max_retries`

Set the retry budget when constructing the client. It applies to both
[`Warmbly`][warmbly.Warmbly] and [`AsyncWarmbly`][warmbly.AsyncWarmbly]:

```python
from warmbly import Warmbly

# Retry up to 5 times per request.
client = Warmbly(api_key="wmbly_...", max_retries=5)

# Disable retries entirely — fail fast.
client = Warmbly(api_key="wmbly_...", max_retries=0)
```

Override it for a single call with the `options` argument. Every resource method
accepts an `options` mapping (`warmbly.RequestOptions`) for per-request
overrides:

```python
# This one request gets a bigger retry budget than the client default.
client.campaigns.create(
    name="Q3 launch",
    options={"max_retries": 8},
)

# ...or none at all.
client.api_keys.list(options={"max_retries": 0})
```

When retries are exhausted, the last failure is raised: a connection problem
becomes [`APIConnectionError`][warmbly.APIConnectionError] (or
[`APITimeoutError`][warmbly.APITimeoutError]); a bad status becomes the matching
[`APIStatusError`][warmbly.APIStatusError] subclass — for example a persistent
`429` ultimately raises [`RateLimitError`][warmbly.RateLimitError].

## Idempotency keys

The SDK makes writes safe to retry by attaching an idempotency key to every
JSON `POST` automatically:

- If you don't supply one, a fresh UUIDv4 is generated and sent as the
  `Idempotency-Key` header.
- The server uses this key to deduplicate, so a retried `POST` (after a timeout
  or a `5xx`, say) won't create a duplicate resource.

To make a retry-across-process-restarts safe, or to deduplicate at the
application level, pass your own key:

```python
# Provide a stable, caller-chosen idempotency key.
client.campaigns.create(
    name="Q3 launch",
    options={"idempotency_key": "campaign-q3-launch-2026"},
)
```

You can also set the header directly via `options["headers"]`; an explicit
`Idempotency-Key` header takes precedence over the auto-generated one:

```python
client.campaigns.create(
    name="Q3 launch",
    options={"headers": {"Idempotency-Key": "campaign-q3-launch-2026"}},
)
```

!!! tip
    Reusing the same idempotency key for two intentionally-distinct creates will
    cause the second to be deduplicated against the first. Use a fresh key per
    logical operation.

## Timeouts

The default timeout is an `httpx.Timeout` of **60 s** overall with a **5 s**
connect timeout. A request that exceeds its timeout raises
[`APITimeoutError`][warmbly.APITimeoutError] — but only after the retry budget is
exhausted, since timeouts are themselves retried.

Configure the timeout on the client. Pass either a single number of seconds or
an `httpx.Timeout` (re-exported as `warmbly.Timeout`) for fine-grained control:

```python
from warmbly import Warmbly, Timeout

# A flat 30-second timeout for every phase of the request.
client = Warmbly(api_key="wmbly_...", timeout=30.0)

# Distinct connect / read / write / pool timeouts.
client = Warmbly(
    api_key="wmbly_...",
    timeout=Timeout(timeout=30.0, connect=5.0),
)
```

Override it per request through `options`:

```python
# Give this slow report query more time.
client.analytics.list(options={"timeout": 120.0})
```

## Putting it together

`max_retries`, `timeout`, and `idempotency_key` are all per-request overridable
through the same `options` mapping, so you can tailor a single risky call without
touching the client defaults:

```python
client.campaigns.create(
    name="Q3 launch",
    options={
        "max_retries": 5,
        "timeout": 45.0,
        "idempotency_key": "campaign-q3-launch-2026",
    },
)
```

The async client behaves identically — the same `options` keys apply, and the
backoff between retries uses non-blocking `await asyncio.sleep(...)` instead of
`time.sleep(...)`.
