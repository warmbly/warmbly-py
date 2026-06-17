# Quickstart

A 60-second tour. By the end you'll have created a client, made a write call,
and iterated a paginated list, in both the sync and async styles.

!!! note "Prerequisites"
    [Install warmbly](install.md) and have a Warmbly API key handy. Export it
    so the client can pick it up automatically:

    ```bash
    export WARMBLY_API_KEY="wmbly_..."
    ```

## Create a client

The client reads `WARMBLY_API_KEY` from the environment, so construction takes
no arguments:

```python
from warmbly import Warmbly

client = Warmbly()
```

Prefer to be explicit? Pass the key (and any other option) directly:

```python
import os
from warmbly import Warmbly

client = Warmbly(api_key=os.environ["WARMBLY_API_KEY"])
```

## Create a campaign

Resource methods return typed [Pydantic models](../guides/pagination.md). Here
`create` returns a `Campaign`; `name` is the only required argument.

```python
campaign = client.campaigns.create(name="Q3 outreach")
print(campaign.id, campaign.status)
print("request id:", campaign.request_id)
```

## Iterate your API keys

List endpoints return a cursor page that transparently fetches every page as
you iterate. Just use a normal `for` loop:

```python
for key in client.api_keys.list():
    print(key.name, key.status)
```

Need to work a page at a time instead? The returned object exposes the raw
fields:

```python
page = client.api_keys.list(limit=20)
print(page.data, page.has_more, page.next_cursor)
```

See the [Pagination guide](../guides/pagination.md) for more.

## Put it together

```python
from warmbly import Warmbly

# Reads WARMBLY_API_KEY from the environment.
client = Warmbly()

campaign = client.campaigns.create(name="Q3 outreach")
print("created campaign:", campaign.id)

for key in client.api_keys.list():
    print(key.name, key.status)
```

## The async mirror

Every method has an `await`-able twin on `AsyncWarmbly`. Swap the class, add
`await`, and iterate lists with `async for`. Using the client as an
`async with` context manager closes the connection pool for you:

```python
import asyncio
from warmbly import AsyncWarmbly


async def main() -> None:
    async with AsyncWarmbly() as client:  # reads WARMBLY_API_KEY
        campaign = await client.campaigns.create(name="Q3 outreach")
        print("created campaign:", campaign.id)

        async for key in client.api_keys.list():
            print(key.name, key.status)


asyncio.run(main())
```

!!! tip "Closing the client"
    If you don't use the `async with` form, call `await client.close()` when
    you're done so the underlying HTTP connections are released. The sync
    `Warmbly` client likewise supports `with Warmbly() as client:` and
    `client.close()`.

## Next steps

- [Authentication](../guides/auth.md): API keys, access tokens, and OAuth2.
- [Async](../guides/async.md): the full async story.
- [Errors](../guides/errors.md) and [Retries](../guides/retries.md).
- [Realtime gateway](../guides/realtime.md): subscribe to live events.
