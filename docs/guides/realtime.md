# Realtime gateway

The **Warmbly realtime gateway** streams live events (campaign progress, email
activity, contact changes, account/warmup status, and bulk-operation updates)
over a single resilient WebSocket connection. The SDK ships a fully managed
client that handles heartbeats, automatic reconnection, session resume, and
event dispatch for you.

Two clients with identical surfaces are provided:

- [`AsyncGatewayClient`][warmbly.AsyncGatewayClient]: the native `asyncio`
  client. Use this from async code.
- [`GatewayClient`][warmbly.GatewayClient]: a blocking facade that runs the
  async client on a background thread, for use from ordinary synchronous code.

Both live in `warmbly` (and `warmbly.gateway`):

```python
from warmbly import AsyncGatewayClient, GatewayClient, GatewayEvent
```

## Authentication and the `realtime_subscribe` scope

The gateway authenticates with a bearer credential passed as `token`: an API
key, an OAuth2 access token, or a session JWT. **The credential must carry the
`realtime_subscribe` scope.** The token is sent in the connection query string
and is never logged.

```python
gateway = AsyncGatewayClient(token="wmbly_...")
```

If the token is missing, invalid, or lacks the required scope, the gateway
rejects the connection with a fatal close code and the client raises
`FatalDisconnect` (see
[Fatal vs. transient failures](#fatal-vs-transient-failures)).

!!! note "Base URL"
    By default the client connects to `wss://realtime.warmbly.com`. Override it
    with `base_url=...` if you target a different environment. The
    `/socket/websocket` path and protocol version query are appended for you.

## A first connection

The usual lifecycle is: **register handlers**, `connect()`, `subscribe()` to one
or more topics, then `run_forever()` to stream events until you `close()`.

```python
import asyncio
from warmbly import AsyncGatewayClient, GatewayEvent


async def main() -> None:
    gateway = AsyncGatewayClient(token="wmbly_...")  # needs realtime_subscribe

    @gateway.on_event(GatewayEvent.CAMPAIGN_STARTED)
    async def on_started(topic: str, payload: dict) -> None:
        print("campaign started:", payload["campaign_id"])

    await gateway.connect()
    await gateway.subscribe("org:00000000-0000-0000-0000-000000000000")
    await gateway.run_forever()  # blocks, supervising reconnects, until close()


asyncio.run(main())
```

`connect()` returns once the socket is open and ready, so any `subscribe()`,
`push()`, or `wait_for()` calls made afterward work immediately. If you only need
to wait for a few events and then stop, you can skip `run_forever()` entirely.
`connect()` already starts the background supervisor that keeps the connection
alive.

## Topics

You subscribe to **topics**, each scoped to a single resource. The topic name is
a prefix plus the resource id:

| Topic | Streams |
|---|---|
| `user:<user_id>` | Events for your own user (inbound email, account connect/disconnect/error, bulk operations). |
| `org:<org_id>` | Org-wide events (campaigns, emails, contacts, accounts/warmup, membership, billing, settings). Supports **intents**, **presence**, and **resume**. |
| `campaign:<campaign_id>` | Per-campaign stats, status changes, progress, and email events. |
| `account:<account_id>` | Per-account sync and warmup-progress events. |
| `bulk:<operation_id>` | Progress and completion for a single bulk operation. |

```python
await gateway.subscribe("user:usr_123")
await gateway.subscribe("org:org_123")
await gateway.subscribe("campaign:cmp_123")
await gateway.subscribe("account:acc_123")
await gateway.subscribe("bulk:op_123")
```

`subscribe()` joins the topic and returns the server's join-reply `response`
object. It raises [`GatewayError`][warmbly.GatewayError] if the join is rejected,
for example because you are not a member of the organization.

### Filtering org events with `intents`

For `org:*` topics you can narrow the firehose with `intents`: substring filters
applied to event types server-side, so the events you do not want never cross
the wire. The server upper-cases the event name and replaces separators with
`_` before matching, which is why a family prefix is enough:

```python
# Only campaign events on this org topic.
await gateway.subscribe("org:org_123", intents=["CAMPAIGN"])

# Two families at once.
await gateway.subscribe("org:org_123", intents=["AUTOMATION", "MEETING"])
```

### Leaving a topic

```python
await gateway.unsubscribe("org:org_123")
```

`unsubscribe()` leaves the topic and drops its tracked presence and resume
state.

## Handling events

### `@on_event`: match an event on any topic

Register a handler for an event name regardless of which topic delivered it.
Handlers receive `(topic, payload)`:

```python
@gateway.on_event(GatewayEvent.EMAIL_OPENED)
async def on_open(topic: str, payload: dict) -> None:
    print(f"{payload['email_account_id']} opened on {topic}")
```

### `@on`: match an exact `(topic, event)` pair

When you only care about one event on one specific topic, register against the
exact tuple:

```python
@gateway.on(("campaign:cmp_123", GatewayEvent.TASK_PROGRESS))
async def on_progress(topic: str, payload: dict) -> None:
    print("progress:", payload)
```

Both decorators return the handler unchanged, so they compose cleanly with other
decorators. Multiple handlers may be registered for the same key; each runs as
its own task, so one slow or failing handler can't stall the receive loop.
Exceptions raised inside a handler are logged, not propagated.

### Event-name constants

[`GatewayEvent`][warmbly.gateway.GatewayEvent] mirrors the server's event
vocabulary as constants so you avoid stringly-typed keys:
`GatewayEvent.CAMPAIGN_STARTED`, `GatewayEvent.EMAIL_OPENED`,
`GatewayEvent.CONTACT_CREATED`, `GatewayEvent.AUTOMATION_RUN`,
`GatewayEvent.MEETING_BOOKED`, `GatewayEvent.AI_DRAFT_READY`, and so on. Unknown
event names still reach `on_event` handlers and `wait_for`, so a server that
adds an event needs no SDK upgrade.

`GatewayEvent.CAMPAIGN_IDLE` is worth knowing about if you run continuous
campaigns: it fires when one runs out of leads and starts waiting for more,
rather than finishing. `GatewayEvent.FORM_SUBMISSION_CREATED` and
`GatewayEvent.PAGE_HIT` cover hosted forms and website tracking, and
`GatewayEvent.ACCOUNT_SYNC_STATE` reports a mailbox's import progress and any
fair-use hold on it.

### `wait_for`: await a single event

Instead of a long-lived handler, you can suspend until the next matching event
arrives. This is handy for request/response-style flows. `wait_for` returns the
event payload:

```python
# Wait for the next BULK_COMPLETED event (any topic), up to 30 seconds.
payload = await gateway.wait_for(GatewayEvent.BULK_COMPLETED, timeout=30)
print("done:", payload)
```

Pass `event=None` to match any event, and an optional `check` predicate
`(topic, payload) -> bool` to narrow further:

```python
payload = await gateway.wait_for(
    GatewayEvent.CAMPAIGN_COMPLETED,
    check=lambda topic, p: p.get("campaign_id") == "cmp_123",
    timeout=60,
)
```

If `timeout` elapses first, `wait_for` raises `asyncio.TimeoutError`.

## Pushing to the server

Some topics accept client-to-server messages. `push()` sends an event with a
payload on a subscribed topic and awaits the reply:

```python
# Liveness ping on a user topic.
reply = await gateway.push("user:usr_123", "ping", {})

# Broadcast your presence on an org topic.
await gateway.push(
    "org:org_123",
    "presence:update",
    {"page": "campaigns", "resource": "cmp_123", "action": "viewing"},
)
```

`push()` returns the reply `response` object and raises
[`GatewayError`][warmbly.GatewayError] if the topic is unknown or the push is
rejected (for example, when in-channel rate limits are exceeded).

## Presence

`org:*` topics track presence: who else is connected and what they are doing.
The gateway sends an initial snapshot followed by incremental deltas, and the
client maintains the merged state for you. Read the current presence map for a
topic at any time with `presence()`:

```python
state = gateway.presence("org:org_123")
for key, record in state.items():
    for meta in record.get("metas", []):
        print(meta.get("name"), meta.get("page"), meta.get("action"))
```

Each meta describes one connected client with fields such as `online_at`,
`name`, `avatar`, `page`, `resource`, and `action`. You can update your own
presence with a `presence:update` push (see above). To react to changes as they
happen, register handlers for `GatewayEvent.PRESENCE_STATE` and
`GatewayEvent.PRESENCE_DIFF`.

## Automatic reconnect and resume

You do not have to manage reconnection. Once `connect()` (or `run_forever()`)
starts the supervisor, the client:

- Runs an application-level **heartbeat** with zombie detection, so a silently
  dead connection is noticed and recycled.
- **Reconnects** on transient drops using exponential backoff with jitter,
  honoring any `retry_after` hint the server sends after rate-limiting.
- **Re-joins** every subscribed topic automatically after a reconnect. Your
  handlers stay registered across the gap.

### Sequence-based resume

For resumable topics (`org:*`), the gateway tags broadcast events with a
monotonic `seq`. The client tracks the highest `seq` it has seen per topic and,
on rejoin, asks the server to replay anything missed during the disconnect. This
is on by default; disable it per subscription with `resume=False`:

```python
await gateway.subscribe("org:org_123")                 # resume on (default)
await gateway.subscribe("org:org_123", resume=False)   # no replay on rejoin
```

If the server cannot honor a resume (for example, the replay buffer has since
been evicted), it reports `resume_failed` and you should fall back to a full
re-sync over the REST API. Hook into that with the `on_resume_failed` callback,
which receives `(topic, payload)`:

```python
async def resync(topic: str, payload: dict) -> None:
    # Re-fetch current state over REST, e.g. client.campaigns.list(...).
    print("resume failed for", topic, "-> re-syncing")

gateway = AsyncGatewayClient(token="wmbly_...", on_resume_failed=resync)
```

### Fatal vs. transient failures

Not every failure is retried. Authentication and permission rejections are
**fatal**: the supervisor will not loop on them, because they require you to fix
the credential and reconnect deliberately. These surface as
`FatalDisconnect` from `connect()` or
`run_forever()`:

```python
from warmbly.gateway import FatalDisconnect

try:
    await gateway.connect()
    await gateway.run_forever()
except FatalDisconnect as exc:
    # e.g. missing/invalid token or missing realtime_subscribe scope
    print("gateway rejected the connection:", exc, "code:", exc.code)
```

Everything else (network blips, server restarts, rate-limit backpressure) is
transient and handled internally by the reconnect loop.

## Lifecycle: `run_forever` and `close`

`run_forever()` blocks for the lifetime of the connection, supervising
reconnects, and returns normally only after `close()`. `close()` is idempotent:
it shuts down the connection, stops reconnecting, and cancels any pending
`wait_for` waiters.

A common pattern is to drive the gateway as a background task and close it on
shutdown:

```python
import asyncio
from warmbly import AsyncGatewayClient, GatewayEvent


async def main() -> None:
    gateway = AsyncGatewayClient(token="wmbly_...")

    @gateway.on_event(GatewayEvent.EMAIL_REPLIED)
    async def on_reply(topic: str, payload: dict) -> None:
        print("reply received:", payload)

    await gateway.connect()
    await gateway.subscribe("org:org_123", intents=["EMAIL"])

    runner = asyncio.create_task(gateway.run_forever())
    try:
        await asyncio.sleep(3600)  # ... do other work, serve requests, etc.
    finally:
        await gateway.close()
        await runner


asyncio.run(main())
```

## The synchronous client

If you are not writing async code, [`GatewayClient`][warmbly.GatewayClient] gives you the same surface
with blocking calls. It runs the async client on a private event loop in a
background thread, and your handlers may be plain (non-`async`) functions:

```python
from warmbly import GatewayClient, GatewayEvent

gateway = GatewayClient(token="wmbly_...")  # needs realtime_subscribe


@gateway.on_event(GatewayEvent.CAMPAIGN_STARTED)
def on_started(topic: str, payload: dict) -> None:  # ordinary function
    print("started:", payload)


gateway.connect()
gateway.subscribe("org:org_123")
gateway.run_forever()  # blocks until close() is called from another thread
```

Every method (`connect`, `subscribe`, `unsubscribe`, `push`, `wait_for`,
`presence`, `run_forever`, and `close`) mirrors the async client but blocks
until it completes. `close()` is safe to call from any thread, including from
inside a synchronous handler, which makes it easy to stop `run_forever()` in
response to an event:

```python
@gateway.on_event(GatewayEvent.BULK_COMPLETED)
def stop(topic: str, payload: dict) -> None:
    gateway.close()  # unblocks run_forever()
```

## See also

- [Webhooks](webhooks.md): for server-to-server delivery when you'd rather
  receive a signed HTTP POST than hold a connection open.
- [Gateway API reference](../reference/gateway.md): full signatures and the
  [`GatewayEvent`][warmbly.gateway.GatewayEvent] constant catalog.
