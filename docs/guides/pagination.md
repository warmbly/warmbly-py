# Pagination

Every Warmbly list endpoint is cursor-paginated. The server returns a single
page shaped like:

```json
{
  "data": [ ... ],
  "pagination": { "total": 1234, "next_cursor": "eyJpZCI6...", "has_more": true }
}
```

Calling a resource's `list()` method gives you a **page object**
(`SyncCursorPage` for the synchronous client, `AsyncCursorPage` for the
asynchronous one). The page knows how to fetch the next page on its own, so most
of the time you can ignore cursors entirely and just iterate.

## Auto-iteration (the common case)

Iterating a page transparently walks **every** page: when the current page is
exhausted, the SDK fetches the next one using the stored `next_cursor` and keeps
going until `has_more` is `false`.

```python
from warmbly import Warmbly

client = Warmbly(api_key="wmbly_...")

# Iterates across all pages, one network round-trip per page, lazily.
for key in client.api_keys.list():
    print(key.id, key.name)
```

`list()` accepts the usual filters plus `limit` (page size). You never pass a
`cursor` yourself when auto-iterating. The SDK threads it through for you:

```python
for contact in client.contacts.list(limit=100):
    ...
```

!!! tip "Stop early whenever you like"
    Because pages are fetched lazily, you can `break` out of the loop at any
    point and no further requests are made.

    ```python
    for campaign in client.campaigns.list():
        if campaign.name == "Q3 launch":
            target = campaign
            break  # no more pages are fetched
    ```

## Working a page at a time

When you want to control fetching yourself, for example to render results page
by page in a UI, or to checkpoint the `next_cursor` to a database, use the page
attributes directly instead of iterating.

A page exposes:

| Attribute / method | Type | Meaning |
| ------------------ | ---- | ------- |
| `.data` | `list[Model]` | The items on **this** page only. |
| `.has_more` | `bool` | Whether the server reports more pages after this one. |
| `.next_cursor` | `str \| None` | The cursor to request the next page. |
| `.total` | `int \| None` | Total matching records, when the server provides it. |
| `.has_next_page()` | `bool` | `True` when both `has_more` is set **and** a `next_cursor` is present. |
| `.get_next_page()` | page | Fetches and returns the next page object. |

```python
page = client.api_keys.list(limit=50)

# Work with just this page's items.
for key in page.data:
    print(key.id)

print(page.total)        # e.g. 1234 (may be None)
print(page.has_more)     # True if another page exists
print(page.next_cursor)  # cursor string, or None

# Advance manually.
while page.has_next_page():
    page = page.get_next_page()
    for key in page.data:
        print(key.id)
```

!!! warning "`get_next_page()` raises when there is no next page"
    Calling `get_next_page()` when `has_next_page()` is `False` raises
    [`WarmblyError`][warmbly.WarmblyError]. Always guard the call with
    `has_next_page()` (or `has_more`), as shown above.

### Persisting a cursor

`next_cursor` is an opaque, JSON-serializable string. You can store it and
resume later by passing it back as `cursor=`:

```python
page = client.contacts.list(limit=100)
save_cursor(page.next_cursor)  # your storage

# ... later, in another process ...
page = client.contacts.list(limit=100, cursor=load_cursor())
```

## Async pagination

The asynchronous client mirrors the sync one: swap `Warmbly` for
[`AsyncWarmbly`][warmbly.AsyncWarmbly] and iterate with `async for`:

```python
import asyncio
from warmbly import AsyncWarmbly

async def main():
    async with AsyncWarmbly(api_key="wmbly_...") as client:
        async for key in client.api_keys.list():
            print(key.id, key.name)

asyncio.run(main())
```

`AsyncWarmbly`'s `list()` returns an awaitable that resolves to the first page,
so you can also fetch and inspect a single page with `await`:

```python
async with AsyncWarmbly(api_key="wmbly_...") as client:
    page = await client.contacts.list(limit=100)

    for contact in page.data:
        print(contact.id)

    while page.has_next_page():
        page = await page.get_next_page()
        for contact in page.data:
            print(contact.id)
```

!!! note "`list()` is not a coroutine: the request is lazy"
    On the async client, `client.x.list(...)` returns immediately without
    sending a request. The HTTP call happens the first time you `await` it or
    start an `async for` over it. This is why you don't write
    `async for ... in await client.x.list()`. Iterate the return value
    directly.

## Sync vs. async at a glance

| | Synchronous (`Warmbly`) | Asynchronous (`AsyncWarmbly`) |
| --- | --- | --- |
| Page type | `SyncCursorPage` | `AsyncCursorPage` |
| Iterate all pages | `for item in client.x.list():` | `async for item in client.x.list():` |
| Get the first page | already eager: `page = client.x.list()` | `page = await client.x.list()` |
| Advance one page | `page = page.get_next_page()` | `page = await page.get_next_page()` |
| Page attributes | `.data` / `.has_more` / `.next_cursor` / `.total` (identical) | same |
