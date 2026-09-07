# Changelog

All notable changes to **warmbly-py** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this
project adheres to [Semantic Versioning](https://semver.org/). Entries are
assembled from news fragments in `changelog/` by
[towncrier](https://towncrier.readthedocs.io/) at release time.

<!-- towncrier release notes start -->

## [v0.3.0] - 2026-09-07

### Added

- Added four resource groups for API surface that shipped since the last sync:
  `segments` (saved contact audiences, with the field catalog, unsaved-definition
  preview, manual include/exclude overrides, and one-off campaign enrolment),
  `forms` (hosted lead-capture forms, their submissions, funnel analytics, brand
  assets, personalized per-contact links, and the custom forms domain),
  `suppressions` (the workspace do-not-contact list), and `ai_tools` (the REST
  tool surface for agents that do not speak MCP, listable in OpenAI
  function-calling shape).
- Exposed the fields and parameters the API gained since the last sync: continuous
  campaigns (`continuous`, `idle_since`), the campaign `kind`, in-body opt-out
  mode, UTM tagging and auto-pause guardrails; contact verification provenance and
  first-touch attribution; mailbox `save_to_sent` and the full tracking-domain
  verdict (`status`, `observed`, `cname_target`); the unibox folder scope on
  `list()` and `mark_seen()`, plus per-folder counts on the overview; the
  `engagement`, `segment_ids` and `verification_status` contact search facets; and
  the `contact_id`, `campaign_id`, `account_id` and `step_id` scoping arguments on
  `campaigns.preview_template()`.
- Filled in the endpoints existing resources were missing: `campaigns.estimate()`,
  `duplicate()`, `list_segments()`, `set_segments()` and `list_forms()`;
  `contacts.list_campaigns()`, `list_segments()`, `verification()` and
  `request_verification()`; the mailbox `allowance()`, `sync()`, `hold()`,
  `release()`, `tracking_domain()`, `verify_tracking_domain()`,
  `refresh_auth_check()`, `behavior()`, `update_behavior()` and `behavior_plan()`
  calls; and `api_keys.revoke_self()`, which lets a credential end its own access
  without the `api_keys` scope.

### Changed

- Added the `CAMPAIGN_IDLE`, `ACCOUNT_SYNC_STATE`, `FORM_SUBMISSION_CREATED` and
  `PAGE_HIT` realtime event constants, and gave `contacts.timeline()` the opaque
  `cursor` parameter that supersedes `before` (which can skip events sharing an
  instant with the page boundary).
- `unibox.thread()` now yields `MessagePreview` rather than `Message`, because
  that is what the endpoint returns: the same row shape as the inbox list, with a
  snippet instead of a body. Reach for `unibox.retrieve()` when you need the body.

### Fixed

- Fixed request and response shapes that never matched the API. `campaigns.create()`
  sent `email_tags`/`folders`, but create names those lists `email_tag_ids` and
  `folder_ids`, so both were silently dropped. `unibox.retrieve()` modelled a
  message under the list-row field names and carried no body at all;
  `unibox.thread()` claimed that same shape where the endpoint returns list rows.
  `ContactTimelineEntry` modelled an `id`/`occurred_at`/`data` envelope the
  timeline has never returned. The `from` key on
  `campaigns.preview_template()` and on analytics reports now populates `from_`,
  which previously stayed `None`.

  Corrected the response models that named fields the API does not return, so the
  typed attributes stop reading `None` where data was in fact delivered: `Plan`
  (`currency`/`interval`/`features` for the real price, duration and limit
  fields), `WarmupBanStatus` (`banned`/`blocklists` for `health_state`,
  `blocked_until` and `pending_appeal`), `CampaignLog` (`level`/`event`/`data` for
  `event_type` and `metadata`), `ContactImportPreview` (`headers`/`rows` for
  `columns`, `has_header` and `sample_rows`), `ContactResearchRun`, `TeamMember`,
  `LeadSyncSource`, `AdvisorSummary` and `OAuthApplication`.
- `nox -s typecheck` now checks `src` only, matching CI. Pointing mypy at the test
  suite as well failed outright, because `tests/conftest.py` and
  `tests/gateway/conftest.py` collide as one module name.


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

