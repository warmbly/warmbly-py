"""Two ways to consume paginated list endpoints."""

from __future__ import annotations

from warmbly import Warmbly


def main() -> None:
    client = Warmbly()

    # 1. Auto-iterate: the SDK fetches each page as you go.
    print("all contacts:")
    for contact in client.contacts.search():
        print("  ", contact.email)

    # 2. Work a page at a time, following the cursor yourself.
    page = client.api_keys.list(limit=50)
    while True:
        for key in page.data:
            print("key:", key.name)
        print(f"(total={page.total}, has_more={page.has_more})")
        if not page.has_next_page():
            break
        page = page.get_next_page()

    client.close()


if __name__ == "__main__":
    main()
