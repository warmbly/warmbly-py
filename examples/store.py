"""Buy a domain and a mailbox, then follow the order until the mailbox connects.

Reading the store needs ``READ_STORE``; quoting and ordering need
``MANAGE_STORE``, and the member behind the key needs ``manage_billing`` for
anything that charges. This charges the workspace for real.
"""

from __future__ import annotations

import os
import time

from warmbly import ConflictError, Warmbly
from warmbly.resources.store import StoreQuote


def main() -> None:
    client = Warmbly(api_key=os.environ["WARMBLY_API_KEY"])

    status = client.store.status()
    if not status.enabled:
        raise SystemExit(f"the store is off here: {status.reason}")
    if not status.plan_active:
        raise SystemExit("buying needs an active paid plan")

    results = client.store.search_domains(q="acmeoutreach", tlds=["com"])
    offer = next((o for o in results.data if o.available), None)
    if offer is None or offer.domain is None:
        raise SystemExit("nothing available; try another name")
    print("buying", offer.domain, "for", (offer.price_micros or 0) / 1e6)

    # Domains are registered under the workspace's registrant, the real legal
    # owner. Save it once with client.store.set_registrant(...) using your own
    # details; this example never invents one.
    if status.registrant is None:
        raise SystemExit("save the workspace's registrant first (set_registrant)")

    quote = client.store.create_quote(
        items=[
            {"type": "domain", "domain": offer.domain, "years": offer.years or 1},
            {
                "type": "mailboxes",
                "domain": offer.domain,
                "provider": status.providers[0],
                "mailboxes": [
                    {"local_part": "ana", "first_name": "Ana", "last_name": "Diaz"}
                ],
            },
        ]
    )
    if quote.due_now_micros is None:
        raise SystemExit("the quote has no total; not ordering")
    due_now = quote.due_now_micros

    def money(micros: int | None) -> str:
        return "unknown" if micros is None else f"{micros / 1e6:.2f} {status.currency}"

    for line in quote.lines:
        print(f"  {line.type} {line.domain}: {money(line.amount_micros)}")
    print(f"due now: {money(due_now)}")
    print(f"mailbox: ana@{offer.domain}")
    print(f"then {money(quote.recurring_monthly_micros)} a month for mailboxes")
    print(f"and {money(quote.yearly_domain_renewal_micros)} a year to renew the domain")
    if input("Place this order? Type 'yes' to confirm: ").strip().lower() != "yes":
        raise SystemExit("not ordered")

    # Order exactly the total that was shown. If the quote expired and the
    # price moved, nothing is charged and the error carries a fresh quote.
    try:
        order = client.store.create_order(
            quote_id=quote.id, expected_due_now_micros=due_now
        )
    except ConflictError as exc:
        if exc.code != "price_changed" or not isinstance(exc.body, dict):
            raise
        fresh = StoreQuote.model_validate(exc.body["details"]["quote"])
        total = (fresh.due_now_micros or 0) / 1e6
        raise SystemExit(f"price changed, new total {total}") from exc

    while order.status in ("charging", "processing"):
        time.sleep(30)
        order = client.store.retrieve_order(order.id)
        print([f"{s.key}:{s.status}" for s in order.steps])

    for mailbox in order.mailboxes:
        print(mailbox.email, mailbox.connect_state, mailbox.action_required)


if __name__ == "__main__":
    main()
