# Changelog

All notable changes to **warmbly-py** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this
project adheres to [Semantic Versioning](https://semver.org/). Entries are
assembled from news fragments in `changelog/` by
[towncrier](https://towncrier.readthedocs.io/) at release time.

<!-- towncrier release notes start -->

## [v0.2.0] - 2026-08-04

First release: synchronous and asynchronous clients, API-key and OAuth2
authentication, the REST resource surface, an OAuth2 client subsystem (PKCE,
refresh, token management), a realtime WebSocket gateway, and webhook signature
verification.

The entries below record how that surface was brought in line with the API
before release; there is no earlier published version to upgrade from.

### Added

- Added multipart support to the transport, so campaign attachments, contact
  CSV imports, and OAuth application logos upload as real files rather than JSON.
  `client.contacts.export()` returns the encoded bytes, so `xlsx` survives intact.
- Added the `ai_agent` and `ai_research` scopes, exported `SCOPES`, `ALL_SCOPES`,
  `READ_ONLY_SCOPES`, and `FULL_ACCESS_SCOPES`, and mapped the status codes the
  API returns but the SDK ignored: `PaymentRequiredError` (402, out of AI
  credits), `NotImplementedAPIError` (501), and `ServiceUnavailableError` (503).
- Added thirteen resource groups covering the rest of the API-key-reachable
  surface: `advisor`, `ai_skills`, `audit_logs`, `automations`, `deliverability`,
  `folders`, `tags`, `categories`, `generation`, `lead_sync`, `meetings`,
  `outreach`, `tasks` (the send dead-letter queue), `warmup_routing`, and `me`.
- Filled in the endpoints existing resources were missing: campaign
  step-layout, overview, and template preview; bulk mailbox tagging; contact
  custom fields and AI research; template duplicate/render/reorder/score; the
  full CRM pipeline, stage, task-type, and faceted deal/task search surface; and
  OAuth application webhook endpoints, deliveries, and logo upload.

### Changed

- `GatewayEvent` now mirrors the server's event vocabulary exactly. Names it
  invented (`CAMPAIGN_PROGRESS`, `EMAIL_BOUNCED`, `MEMBER_ADDED`, ...) are gone,
  and the automation, meeting, AI, billing, audit, and notification families it
  was missing are present.

### Removed

- Removed `plans.retrieve()` and the OAuth `client_credentials` grant. Neither
  exists on the server: there is no per-plan route, and the token endpoint accepts
  only `authorization_code` and `refresh_token`.

### Fixed

- Corrected request shapes that did not match the API: `emails.send` takes a
  recipient list and `body_html`/`body_plain`; `emails.track` passes the domain as
  a query parameter; `campaigns.create_step` takes no body; `contacts.create` and
  `contacts.bulk_delete` take bare arrays; `templates` uses `body_html`/
  `body_plain`; and CRM deals use `stage_id`/`value` rather than `stage`/`amount`.
- Fixed list methods that assumed a `data` envelope on endpoints that name their
  collection differently (`plans`, `webhooks`, `oauth/applications`,
  `integrations`, `automations`, `warmup/routing`) or return a bare array
  (`crm/pipelines`, a contact's deals). They silently returned nothing.
- Rewrote the `teams` resource. It targeted `/teams/members`, `/teams/invitations`,
  and `/teams/roles`, none of which exist; teams are CRUD at `/teams` with
  membership managed per team.
- Rewrote the `unibox` resource against the real routes. It previously targeted
  `/unibox/threads/*`, which does not exist, so every call 404'd. The inbox is
  message-centric: `list()`, `retrieve()`, and `thread()` replace the old thread
  methods, alongside compose, drafts, agent drafts, snoozes, labels, and
  scheduled sends.
- `verify_webhook_signature` now implements the scheme the gateway actually uses:
  `X-Warmbly-Signature: t=<unix>,v1=<hex>`, digesting `"{t}.{raw_body}"`. It
  previously computed a bare `sha256=<hex>` over the body alone and would have
  rejected every real delivery. It also enforces a 300-second replay window
  (override with `tolerance=`) and accepts multiple `v1` digests during a secret
  rotation.

