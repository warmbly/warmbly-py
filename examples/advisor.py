"""Read the Advisor's findings and act on them.

The Advisor runs detectors across the organization and surfaces findings on the
row they are about. Each carries a severity and an explanation, and many carry
an ``action`` the server can apply for you.

Findings are stateful: applying, snoozing, or dismissing one sticks until the
underlying condition clears and recurs, so "this is fine" is said once.
"""

from __future__ import annotations

from warmbly import Warmbly


def main() -> None:
    client = Warmbly()

    summary = client.advisor.summary()
    print(
        f"health {summary.score}/100 — {summary.critical} critical, {summary.high} high"
    )

    settings = client.advisor.settings()
    if not settings.enabled:
        print("advisor is off for this organization")
        client.close()
        return

    for finding in client.advisor.list(category="deliverability"):
        print(f"[{finding.severity}] {finding.title} — {finding.entity_label}")
        print("   ", finding.detail)

        if finding.action is not None:
            # The Advisor can fix this one itself. `preview` on the action
            # describes exactly what would change.
            applied = client.advisor.apply(finding.id)
            print("    applied:", applied.applied_result)

            # Undo is available if it turns out to be wrong.
            # client.advisor.undo(finding.id)
        elif finding.agent_fixable:
            # Only the AI assistant can resolve this, and that path is
            # session-only, so surface it to a human instead.
            print("    needs the assistant — open it in the dashboard")
        else:
            # Not actionable right now: hide it for a week.
            client.advisor.snooze(finding.id, days=7)

        # Tell the Advisor whether the finding was worth surfacing.
        client.advisor.feedback(finding.id, helpful=True)

    # Re-evaluate after making changes. Detection runs in the background, so the
    # returned summary may still reflect the previous pass.
    print("refreshed score:", client.advisor.refresh().score)

    client.close()


if __name__ == "__main__":
    main()
