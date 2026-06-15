# Errors

Everything the SDK raises descends from a single base class,
[`WarmblyError`][warmbly.WarmblyError], so you can catch every SDK-originated
failure with one `except`. Below that root, HTTP failures map onto per-status
subclasses that carry the request id, status code, headers, and parsed body.

!!! info "`httpx` never leaks out"
    The transport extracts plain values (status code, headers, parsed body)
    before constructing an exception. No `httpx` exception or response object is
    ever stored on or raised from an SDK error, so you only ever need to catch
    `warmbly` types.

## The exception tree

```text
WarmblyError                     # base — catches everything below
├── APIError                     # any error from an API interaction
│   ├── APIConnectionError       # could not reach the server
│   │   └── APITimeoutError      # request exceeded the timeout
│   ├── APIResponseValidationError   # 2xx body failed to parse into a model
│   └── APIStatusError           # server returned a non-2xx status
│       ├── BadRequestError          # 400
│       ├── AuthenticationError      # 401
│       ├── PermissionDeniedError    # 403
│       ├── NotFoundError            # 404
│       ├── ConflictError            # 409
│       ├── UnprocessableEntityError # 422
│       ├── RateLimitError           # 429
│       └── InternalServerError      # 5xx
├── OAuthError                   # OAuth2 token-endpoint error (RFC 6749)
└── GatewayError                 # realtime gateway error
```

All of these are importable from the top-level package:

```python
from warmbly import (
    WarmblyError,
    APIError,
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
    BadRequestError,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    ConflictError,
    UnprocessableEntityError,
    RateLimitError,
    InternalServerError,
    OAuthError,
    GatewayError,
)
```

## Status code → exception

The SDK picks the most specific subclass for the response status. Statuses with
no dedicated class become `InternalServerError` (5xx) or the generic
`APIStatusError` (any other non-2xx).

| Status | Exception | When it happens |
| ------ | --------- | --------------- |
| 400 | `BadRequestError` | Malformed request. |
| 401 | `AuthenticationError` | Missing or invalid API key / token. |
| 403 | `PermissionDeniedError` | Authenticated, but not allowed to do this. |
| 404 | `NotFoundError` | The resource does not exist. |
| 409 | `ConflictError` | State conflict (e.g. duplicate / version mismatch). |
| 422 | `UnprocessableEntityError` | Semantically invalid request. |
| 429 | `RateLimitError` | Rate limit exceeded — see `.retry_after`. |
| 5xx | `InternalServerError` | Server-side failure. |
| other non-2xx | `APIStatusError` | Anything without a dedicated subclass. |

## Catching specific errors

Catch the precise subclass you want to handle, and let the rest propagate (or
fall through to a broad `except WarmblyError`). Because the tree is
single-rooted, ordering from most specific to least specific works as expected:

```python
from warmbly import (
    Warmbly,
    NotFoundError,
    RateLimitError,
    APIStatusError,
    APIConnectionError,
    WarmblyError,
)

client = Warmbly(api_key="wmbly_...")

try:
    key = client.api_keys.retrieve("ak_does_not_exist")
except NotFoundError:
    key = None  # handle the 404 specifically
except RateLimitError as exc:
    # back off using the server's hint, if present
    wait_for(exc.retry_after or 1.0)
except APIStatusError as exc:
    # any other non-2xx (400/401/403/409/422/5xx/...)
    log.error("API returned %s: %s", exc.status_code, exc.message)
except APIConnectionError:
    # never reached the server (DNS, refused, reset, timeout)
    raise
except WarmblyError:
    # belt-and-braces catch-all for anything else from the SDK
    raise
```

To handle a whole family at once, catch a parent. For example, catching
`APIStatusError` covers every HTTP status error; catching `APIConnectionError`
covers both connection failures and timeouts (since `APITimeoutError` is a
subclass).

## Inspecting an error

[`APIStatusError`][warmbly.APIStatusError] and its subclasses expose the details
you need for logging, debugging, and support tickets:

```python
try:
    client.campaigns.create(name="")
except APIStatusError as exc:
    print(exc.status_code)  # int, e.g. 422
    print(exc.message)      # human-readable message from the error envelope
    print(exc.request_id)   # X-Request-Id header — quote this to support
    print(exc.code)         # machine-readable "code" from the body, if any
    print(exc.body)         # parsed response body (dict, or raw text)
    print(exc.headers)      # response headers as a plain mapping
    print(str(exc))         # "[422] <message> (request_id: <id>)"
```

| Attribute | Available on | Description |
| --------- | ------------ | ----------- |
| `.status_code` | `APIStatusError` | The HTTP status code (`int`). |
| `.request_id` | `APIStatusError` | The `X-Request-Id` header value (`str \| None`). |
| `.headers` | `APIStatusError` | Response headers as a `Mapping[str, str]`. |
| `.message` | `APIError` | Human-readable message (from `message`/`error` in the body). |
| `.body` | `APIError` | Parsed JSON body (`dict`), or raw text, or `None`. |
| `.code` | `APIError` | The `code` field from the error envelope, if present. |
| `.retry_after` | `RateLimitError` | Seconds to wait before retrying (`float \| None`). |

The backend error envelope looks like `{"error", "message", "code",
"request_id"}`; `.message` and `.code` are pulled from it automatically, and
`.request_id` comes from the response header.

## Rate limits and `retry_after`

A 429 raises [`RateLimitError`][warmbly.RateLimitError], which adds a
`retry_after` attribute — the number of seconds to wait before trying again. It
is parsed from the `Retry-After` response header (numeric seconds or an
HTTP-date) or from a `retry_after` field in the body, and is `None` when neither
is provided.

```python
import time
from warmbly import RateLimitError

try:
    client.emails.list()
except RateLimitError as exc:
    delay = exc.retry_after if exc.retry_after is not None else 1.0
    time.sleep(delay)
    # ... then retry
```

!!! tip "The SDK already retries 429s for you"
    You usually won't see `RateLimitError` for transient throttling: the client
    automatically retries `429` (honoring `Retry-After`) up to `max_retries`
    times. The exception surfaces only after retries are exhausted. See the
    [Retries guide](retries.md).

## Connection errors and timeouts

When a request can't reach the server, the SDK raises
[`APIConnectionError`][warmbly.APIConnectionError]. When it reaches the server
but exceeds the configured timeout, it raises
[`APITimeoutError`][warmbly.APITimeoutError] (a subclass of
`APIConnectionError`). Both preserve the originating exception via `__cause__`:

```python
from warmbly import APITimeoutError, APIConnectionError

try:
    client.contacts.list()
except APITimeoutError:
    print("request timed out")
except APIConnectionError as exc:
    print("could not reach Warmbly:", exc.__cause__)
```

## OAuth errors

Token-endpoint failures from [`warmbly.oauth`](oauth.md) raise
[`OAuthError`][warmbly.OAuthError] rather than an HTTP status error. It follows
the RFC 6749 `{error, error_description}` shape:

```python
from warmbly import OAuthError
from warmbly.oauth import OAuth2Client

oauth = OAuth2Client(client_id="...", client_secret="...")

try:
    token = oauth.exchange_code(code, code_verifier=verifier)
except OAuthError as exc:
    print(exc.error)              # e.g. "invalid_grant", "invalid_client"
    print(exc.error_description)  # human-readable detail, if provided
```
