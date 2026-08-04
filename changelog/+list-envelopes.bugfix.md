Fixed list methods that assumed a `data` envelope on endpoints that name their
collection differently (`plans`, `webhooks`, `oauth/applications`,
`integrations`, `automations`, `warmup/routing`) or return a bare array
(`crm/pipelines`, a contact's deals). They silently returned nothing.
