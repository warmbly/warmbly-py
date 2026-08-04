Corrected request shapes that did not match the API: `emails.send` takes a
recipient list and `body_html`/`body_plain`; `emails.track` passes the domain as
a query parameter; `campaigns.create_step` takes no body; `contacts.create` and
`contacts.bulk_delete` take bare arrays; `templates` uses `body_html`/
`body_plain`; and CRM deals use `stage_id`/`value` rather than `stage`/`amount`.
