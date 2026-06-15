# Client

The top-level entry points to the SDK. Construct a [`Warmbly`][warmbly.Warmbly]
for ordinary synchronous code, or an [`AsyncWarmbly`][warmbly.AsyncWarmbly] for
`asyncio`. Both accept the same constructor arguments and expose the same typed
resource groups (the async variant mirrors every resource with its `Async*`
counterpart).

```python
from warmbly import Warmbly

client = Warmbly(api_key="wmbly_...")  # or set WARMBLY_API_KEY
campaign = client.campaigns.retrieve("camp_123")
```

```python
import asyncio
from warmbly import AsyncWarmbly

async def main() -> None:
    async with AsyncWarmbly() as client:
        campaign = await client.campaigns.retrieve("camp_123")

asyncio.run(main())
```

## Warmbly

::: warmbly.Warmbly

## AsyncWarmbly

::: warmbly.AsyncWarmbly
