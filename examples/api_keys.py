"""Create, manage, and audit API keys.

The plaintext ``secret`` is returned ONLY on the create response — store it
immediately, because it cannot be retrieved again.
"""

from __future__ import annotations

from warmbly import Warmbly, scopes_to_mask


def main() -> None:
    client = Warmbly()

    # Create a key scoped to exactly the permissions it needs.
    created = client.api_keys.create(
        name="reporting-bot",
        permissions=scopes_to_mask(["read_campaigns", "read_analytics"]),
        rate_limit_per_minute=120,
        description="Read-only key for the analytics dashboard",
    )
    print("created:", created.id)
    print("SECRET (shown once):", created.secret)

    # List keys (auto-paginates).
    for key in client.api_keys.list():
        print(f"  {key.name}: {key.status}")

    # Inspect available permissions and presets.
    catalog = client.api_keys.permissions()
    print("available permissions:", len(catalog.permissions))

    # Org-wide usage summary, and per-key analytics.
    summary = client.api_keys.usage_summary()
    print("requests (24h):", summary.requests_24h)
    analytics = client.api_keys.analytics(created.id)
    print("buckets:", len(analytics.buckets))

    # Tighten the rate limit later.
    client.api_keys.update(created.id, rate_limit_per_minute=60)

    # Revoke when you're done with it.
    client.api_keys.delete(created.id, reason="example cleanup")
    print("revoked", created.id)

    client.close()


if __name__ == "__main__":
    main()
