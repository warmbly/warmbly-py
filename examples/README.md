# warmbly-py examples

Runnable, self-contained examples covering the whole SDK. Each script reads your
API key from the `WARMBLY_API_KEY` environment variable (the OAuth examples use
their own credentials).

```bash
export WARMBLY_API_KEY="wmbly_..."
pip install warmbly            # add [oauth] for the token-storage example
python examples/quickstart.py
```

| Example | What it shows |
|---|---|
| [`quickstart.py`](./quickstart.py) | The 60-second tour: client, a write, a paginated read |
| [`api_keys.py`](./api_keys.py) | Create / list / update / revoke API keys, permissions, usage |
| [`scopes.py`](./scopes.py) | Convert between scope names and the permission bitmask |
| [`oauth_applications.py`](./oauth_applications.py) | Register and manage OAuth2 applications |
| [`oauth_flow.py`](./oauth_flow.py) | Full authorization-code + PKCE flow, refresh, revoke |
| [`oauth_token_manager.py`](./oauth_token_manager.py) | Persistent storage + automatic token refresh |
| [`campaigns.py`](./campaigns.py) | Create a campaign, add steps, start/stop, read logs |
| [`email_accounts.py`](./email_accounts.py) | Manage mailboxes, warmup controls, send an email |
| [`contacts.py`](./contacts.py) | Search, bulk add, CSV import/export, notes |
| [`unibox.py`](./unibox.py) | Read the inbox, label, AI-draft, reply, schedule sends |
| [`crm.py`](./crm.py) | Pipelines and stages, deals, tasks, faceted search + summaries |
| [`advisor.py`](./advisor.py) | Read deliverability findings and apply the fixes |
| [`pagination.py`](./pagination.py) | Auto-iterate every page, or walk pages manually |
| [`error_handling.py`](./error_handling.py) | The exception hierarchy, rate limits, retries, timeouts |
| [`async_usage.py`](./async_usage.py) | `AsyncWarmbly`, `async for`, concurrent requests |
| [`realtime_gateway_async.py`](./realtime_gateway_async.py) | Subscribe to live events (asyncio) |
| [`realtime_gateway_sync.py`](./realtime_gateway_sync.py) | The same, with the blocking sync client |
| [`webhooks.py`](./webhooks.py) | Verify inbound webhook signatures and manage endpoints |

> These call the real API. Run them against a test organization, and note that
> `campaigns.start(...)`, `emails.send(...)`, and `unibox.reply(...)` actually
> send mail. The AI endpoints (`generation.*`, `contacts.research()`,
> `unibox.draft_reply()`) spend credits.
