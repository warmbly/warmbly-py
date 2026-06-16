# Async

[`AsyncWarmbly`][warmbly.AsyncWarmbly] is the asynchronous twin of
[`Warmbly`][warmbly.Warmbly]. It exposes exactly the same resources and methods,
but every network call is a coroutine you `await`, and list endpoints are
iterated with `async for`. Use it when your application already runs on
`asyncio` (or `anyio`/`trio`) and you want non-blocking I/O and easy concurrency.

```python
import asyncio
from warmbly import AsyncWarmbly


async def main():
    client = AsyncWarmbly(api_key="wmbly_...")
    campaign = await client.campaigns.retrieve("camp_123")
    print(campaign.name)
    await client.close()


asyncio.run(main())
```

The constructor takes the same arguments as the sync client (`api_key`,
`base_url`, `timeout`, `max_retries`) and reads `WARMBLY_API_KEY` /
`WARMBLY_BASE_URL` from the environment in the same way. See
[Authentication](auth.md) for the details.

## Awaiting calls

Every resource method that performs a request returns a coroutine, so it must be
`await`ed:

```python
client = AsyncWarmbly(api_key="wmbly_...")

campaign = await client.campaigns.create(name="Q3 outreach")
campaign = await client.campaigns.retrieve(campaign.id)
await client.campaigns.delete(campaign.id)
```

Calling such a method without `await` returns an un-awaited coroutine and does
no work, a common first mistake.

## Paginating with `async for`

`list()` on the async client returns an [`AsyncCursorPage`][warmbly.AsyncWarmbly]
that transparently fetches subsequent pages. Iterate it with `async for`, and
every item across all pages is yielded in turn:

```python
async for campaign in client.campaigns.list():
    print(campaign.id, campaign.name)
```

The async `list()` is special: it is returned **un-awaited** so you can iterate
it directly with `async for`. If you only want the first page, you may also
`await` it to get a concrete page object and inspect its fields:

```python
page = await client.campaigns.list(limit=50)
print(page.total, page.has_more)
for campaign in page.data:          # page.data is a plain list; use `for`
    print(campaign.id)

# Fetch the next page manually:
if page.has_next_page():
    page = await page.get_next_page()
```

See the [Pagination guide](pagination.md) for the full page API.

## Closing the client

The async client owns an `httpx.AsyncClient` connection pool that must be closed.
Either `await client.close()` explicitly, or (preferably) use the client as an
`async with` context manager so it is closed automatically, even on error:

```python
import asyncio
from warmbly import AsyncWarmbly


async def main():
    async with AsyncWarmbly(api_key="wmbly_...") as client:
        async for contact in client.contacts.list():
            print(contact.id)
    # the connection pool is closed here


asyncio.run(main())
```

If you construct the client without `async with`, remember the cleanup:

```python
client = AsyncWarmbly(api_key="wmbly_...")
try:
    await client.emails.list()
finally:
    await client.close()
```

## Concurrency with `asyncio.gather`

The biggest payoff of the async client is running many requests concurrently
over a single connection pool. Use `asyncio.gather` to await several coroutines
at once:

```python
import asyncio
from warmbly import AsyncWarmbly


async def main():
    async with AsyncWarmbly(api_key="wmbly_...") as client:
        ids = ["camp_1", "camp_2", "camp_3"]
        campaigns = await asyncio.gather(
            *(client.campaigns.retrieve(cid) for cid in ids)
        )
        for campaign in campaigns:
            print(campaign.id, campaign.name)


asyncio.run(main())
```

`gather` returns results in the same order as the input coroutines. If any call
raises, `gather` re-raises the first exception; pass `return_exceptions=True` to
collect failures alongside successes instead:

```python
results = await asyncio.gather(
    *(client.campaigns.retrieve(cid) for cid in ids),
    return_exceptions=True,
)
for cid, result in zip(ids, results):
    if isinstance(result, Exception):
        print(f"{cid} failed: {result}")
    else:
        print(f"{cid}: {result.name}")
```

!!! tip "Bound your concurrency"
    Firing thousands of requests at once can exhaust the connection pool and
    trip rate limits ([`RateLimitError`][warmbly.RateLimitError]). Cap
    in-flight work with an `asyncio.Semaphore`:

    ```python
    sem = asyncio.Semaphore(10)

    async def fetch(cid):
        async with sem:
            return await client.campaigns.retrieve(cid)

    campaigns = await asyncio.gather(*(fetch(cid) for cid in ids))
    ```

Reuse a single `AsyncWarmbly` instance across all the concurrent tasks (it is
designed to share one pooled HTTP client) rather than creating a client per
request.

## Async OAuth2

The OAuth2 subsystem has async equivalents too:
[`AsyncOAuth2Client`][warmbly.oauth.AsyncOAuth2Client] (with awaitable
`exchange_code`, `refresh_token`, `client_credentials`, and `revoke`) and
[`AsyncTokenManager`][warmbly.oauth.AsyncTokenManager]. `authorization_url` stays
synchronous because it performs no I/O. See the [OAuth2 guide](oauth.md) for the
full flow.

```python
from warmbly import AsyncWarmbly
from warmbly.oauth import AsyncOAuth2Client

async with AsyncOAuth2Client(
    client_id="wmcid_...",
    client_secret="wmcs_...",
    redirect_uri="https://app.example.com/callback",
) as oauth:
    token = await oauth.exchange_code(code, code_verifier=verifier)

async with AsyncWarmbly(api_key=token.access_token) as api:
    async for campaign in api.campaigns.list():
        print(campaign.id)
```
