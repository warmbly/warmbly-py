"""Run an inbox placement test from one mailbox and read the verdict."""

from warmbly import Warmbly

client = Warmbly()  # reads WARMBLY_API_KEY

overview = client.placement.overview()
print(overview)

# Needs the send_campaigns permission; seed mailboxes receive the probe.
tests = client.placement.create_tests(
    sender_account_id="acc_123",
    subject="Quick question",
    body_plain="Hi there, just checking in.",
)
for test in tests:
    detail = client.placement.retrieve_test(test.id)
    print(detail.id, detail.status)
