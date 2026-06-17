"""The 60-second tour: construct a client, make a write, read a paginated list.

export WARMBLY_API_KEY="wmbly_..."
python examples/quickstart.py
"""

from __future__ import annotations

from warmbly import Warmbly


def main() -> None:
    # api_key defaults to the WARMBLY_API_KEY environment variable.
    client = Warmbly()

    # Create something (responses are typed pydantic models).
    campaign = client.campaigns.create(name="Q3 outreach")
    print(f"created campaign {campaign.id!r} (status={campaign.status})")
    print("request id:", campaign.request_id)  # handy for support tickets

    # Read a list. Iterating transparently walks every page.
    print("\nyour API keys:")
    for key in client.api_keys.list():
        print(f"  - {key.name}: {key.key_prefix}…{key.key_suffix} ({key.status})")

    client.close()


if __name__ == "__main__":
    main()
