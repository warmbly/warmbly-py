# Authentication

Every request to the Warmbly API is authenticated with a bearer credential. The
SDK accepts that credential through the `api_key` argument on the
[`Warmbly`][warmbly.Warmbly] / [`AsyncWarmbly`][warmbly.AsyncWarmbly] client and
sends it on every request as `Authorization: Bearer <credential>`.

Warmbly recognizes two kinds of credential, and the client treats them
identically:

| Credential | Prefix | How you get it | Best for |
| ---------- | ------ | -------------- | -------- |
| **API key** | `wmbly_…` | Created in the dashboard, or via `client.api_keys.create(...)` | Server-side scripts, your own backend, cron jobs |
| **OAuth2 access token** | `wmat_…` | Obtained through an OAuth2 flow (see the [OAuth2 guide](oauth.md)) | Acting on behalf of *another* Warmbly user/organization |

Both are passed the same way:

```python
from warmbly import Warmbly

client = Warmbly(api_key="wmbly_...")          # an API key
client = Warmbly(api_key="wmat_...")           # an OAuth2 access token
```

Pick an **API key** when your code acts as itself. Pick an **OAuth2 access
token** when your application acts on behalf of a user who granted you access.
That token is short-lived (one hour) and should be kept fresh with the helpers
described in the [OAuth2 guide](oauth.md).

## Passing the credential explicitly

The most direct option is to pass `api_key` to the constructor:

```python
from warmbly import Warmbly

client = Warmbly(api_key="wmbly_your_key_here")

for key in client.api_keys.list():
    print(key.id)
```

The same argument name is used regardless of credential type. An OAuth2 access
token goes in the very same slot:

```python
client = Warmbly(api_key=access_token)  # access_token is a wmat_... string
```

!!! tip "Keep secrets out of source"
    Never hard-code a credential in code that lands in version control. Prefer
    the environment variable below, a secrets manager, or (for OAuth2) the
    [token storage backends](oauth.md#token-storage).

## Using the `WARMBLY_API_KEY` environment variable

If you omit `api_key`, the client falls back to the `WARMBLY_API_KEY`
environment variable:

```bash
export WARMBLY_API_KEY="wmbly_your_key_here"
```

```python
from warmbly import Warmbly

client = Warmbly()  # reads WARMBLY_API_KEY from the environment
```

If neither an explicit `api_key` nor the environment variable is present, the
constructor raises a [`WarmblyError`][warmbly.WarmblyError]:

```text
No API key provided. Pass api_key=... or set the WARMBLY_API_KEY
environment variable.
```

An explicit `api_key=` argument always takes precedence over the environment
variable.

## Overriding the base URL

By default the client talks to production at `https://api.warmbly.com/v1`. You
can point it elsewhere (a staging environment, a local mock, or a proxy) with
the `base_url` argument:

```python
from warmbly import Warmbly

client = Warmbly(
    api_key="wmbly_...",
    base_url="https://staging.warmbly.com/v1",
)
```

The base URL is resolved in this order:

1. The explicit `base_url=` argument.
2. The `WARMBLY_BASE_URL` environment variable.
3. The production default, `https://api.warmbly.com/v1`.

```bash
export WARMBLY_BASE_URL="https://staging.warmbly.com/v1"
```

```python
client = Warmbly(api_key="wmbly_...")  # uses WARMBLY_BASE_URL if set
```

## Other client options

The constructor also accepts a per-request `timeout` and a `max_retries` count:

```python
import httpx
from warmbly import Warmbly

client = Warmbly(
    api_key="wmbly_...",
    timeout=30.0,                       # seconds, or an httpx.Timeout
    max_retries=5,                      # default is 2
)

# Fine-grained timeouts via httpx.Timeout:
client = Warmbly(
    api_key="wmbly_...",
    timeout=httpx.Timeout(60.0, connect=5.0),
)
```

See the [Retries guide](retries.md) for the retry policy and the
[Async guide](async.md) for the asynchronous client.

## Scopes and permission bitmasks

Warmbly expresses permissions both as readable scope strings (such as
`"read_campaigns"`) and as a single integer bitmask. OAuth2 application
registration and API-key creation both expect the **integer** form, so the SDK
ships two converters:

- [`scopes_to_mask(names)`][warmbly.scopes_to_mask]: turn a list of scope
  strings into the bitmask.
- [`mask_to_scopes(mask)`][warmbly.mask_to_scopes]: turn a bitmask back into
  the list of scope names it grants.

```python
from warmbly import scopes_to_mask, mask_to_scopes

mask = scopes_to_mask(["read_campaigns", "write_campaigns", "send_campaigns"])
# mask is an int that combines those permission bits

mask_to_scopes(mask)
# ['read_campaigns', 'write_campaigns', 'send_campaigns']
```

Use the mask wherever the API wants an integer, for example, creating an API
key with `client.api_keys.create(..., permissions=...)`:

```python
key = client.api_keys.create(
    name="reporting-bot",
    permissions=scopes_to_mask(["read_campaigns", "read_analytics"]),
)
print(key.id)
```

`scopes_to_mask` raises `ValueError` for an unrecognized scope name, so a typo
fails fast rather than silently granting the wrong permissions.

The recognized scope names are:

```
read_emails        read_campaigns    read_contacts     read_unibox
read_analytics     write_emails      write_campaigns   write_contacts
write_unibox       bulk_contacts     bulk_campaigns    realtime_subscribe
webhooks           api_keys          send_campaigns    read_templates
write_templates    read_crm          write_crm         read_audit_logs
integrations       warmup_routing    ai_agent          ai_research
```

Three presets are exported for the common cases, matching the ones the
dashboard offers:

```python
from warmbly import ALL_SCOPES, READ_ONLY_SCOPES, FULL_ACCESS_SCOPES, SCOPES

READ_ONLY_SCOPES    # every read_* scope and nothing else
FULL_ACCESS_SCOPES  # every scope (same as ALL_SCOPES)
SCOPES              # the name -> bit mapping, if you want to build your own
```

The same scope strings are used when requesting OAuth2 authorization. See the
[OAuth2 guide](oauth.md).
