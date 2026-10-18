# Changelog

All notable changes to **warmbly-py** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this
project adheres to [Semantic Versioning](https://semver.org/). Entries are
assembled from news fragments in `changelog/` by
[towncrier](https://towncrier.readthedocs.io/) at release time.

<!-- towncrier release notes start -->

## [v0.4.0] - 2026-10-18

### Added

- API keys gain `delete_permanently` to remove a revoked or expired key and its usage logs, and the permissions catalog reports `grantable` and `app_scopes`.
- Added `analytics.direct()` (`GET /analytics/direct`) for hand-written mail volume, replies and tracking, `analytics.inbox_tagging()` (`GET /analytics/inbox-tagging`) for reviewing automatic inbox tagging, and `analytics.warmup_placement()` (`GET /analytics/warmup/placement`) for where warmup mail landed, each returning typed models.
- Added `campaigns.lead_cc()`, `set_lead_cc()` and `suggest_lead_cc()` (`GET`/`PUT /campaigns/:id/leads/:contactId/cc` and `GET .../cc/suggestions`) to read, replace and get suggestions for the contacts copied on every email a campaign sends one lead.
- Added `campaigns.lead_hold()`, `pause_lead()` and `resume_lead()` (`GET /campaigns/:id/leads/:contactId/hold`, `POST .../pause`, `POST .../resume`) to park one contact inside one campaign, optionally until a date, without unsubscribing them. Each returns a `CampaignLeadHoldState` whose `hold` is `None` when the lead is not held.
- Added `campaigns.placement_monitor()`, `put_placement_monitor()` and `delete_placement_monitor()` (`GET`/`PUT`/`DELETE /campaigns/:id/placement-monitor`) to manage a campaign's scheduled inbox placement test. `placement_monitor()` returns a result whose `data` is `None` when the campaign has no monitor.
- Added `campaigns.send_plan()` (`GET /campaigns/:id/send-plan`), returning a typed `CampaignSendPlan` with today's projected volume, the limits that decided it, the sending window, lead supply and each mailbox's day.
- Added `emails.identity()` (`GET /emails/:id/identity`) and `emails.refresh_identity()` (`POST /emails/:id/identity/refresh`, with an optional `import_signature`) to read and refresh the addresses a mailbox may send as and where its signature came from.
- Added `emails.update_direct_tracking()` (`PATCH /emails/:id/direct-tracking`) to switch open and click tracking on a mailbox's hand-written unibox sends, returning the stored `track_direct_mail` value.
- Added `emails.update_sync()` (`PUT /emails/:id/sync`) to replace the folders a mailbox's sync skips. `emails.sync()` now also returns `skip_folders`, the listed `folders`, `policy.skip_folders` and the `folders_skipped_cap` and `folders_skipped_conflict` counts.
- Added the `placement` resource (`client.placement`, sync and async) for inbox placement tests: `overview`, `coverage`, `list_tests`, `retrieve_test`, `create_tests`, `cancel_test`, `list_seeds`, `set_seed`, and batches that run one test from many mailboxes with `preview_batch`, `create_batch`, `list_batches`, `retrieve_batch`, `list_batch_senders` and `cancel_batch`. The routes wrap results in a `data` envelope, which the methods unwrap into typed models.
- Contacts gains `salesforce`, `sync_salesforce` and `unlink_salesforce` for a contact's Salesforce panel, with typed panel, record, opportunity and task models.
- Contacts gains background imports: `list_imports`, `create_import` (multipart upload), `retrieve_import`, `save_import_draft`, `analyze_import`, `start_import`, `cancel_import` and `download_import_failures`, with `ContactImport` and `ContactImportAnalysis` models. The preview now reports `mapping_source`, `inferred_columns` and `column_stats`, and the synchronous commit result reports `segments_pinned`.
- Forms gain submission triage: `forms.update(triage_enabled=...)`, `Form.triage_enabled`, `FormsConfig.triage_available`, and `FormSubmission.triage` and `triage_confidence`.
- Lead sync sources can pin synced rows into segments: `lead_sync.create_source()` and `update_source()` take `segment_ids`, `list_sources()` takes `segment_id`, and `LeadSyncSource` exposes `segment_ids`.
- Templates gains `analyze`, the AI spam analysis, which returns findings with the quoted fragment and a suggested fix, a suggested subject, the rules score and a copy judgment, and charges AI credits. `TemplateScore` no longer declares the `grade` and `suggestions` fields the server never sent.
- The `crm` resource covers connected CRM mode (HubSpot and Pipedrive): `settings()` and `update_settings()`, `metadata()`, `owners()` and `map_owner()`, `sync_health()`, `sync_now()`, `retry_sync_failures()` and `discard_sync_failures()`, `backfill_preview()` and `start_backfill()`, the contact record calls `retrieve_contact()`, `refresh_contact()`, `link_contact()` and `update_contact()`, and list imports with `lists()`, `preview_list_import()` and `import_list()`, each returning typed models.
- The new `email_images` resource lists, uploads (multipart) and deletes the workspace images hosted for email bodies.
- Unibox gains `move_folder` to archive, trash or restore messages and whole conversations. `mark_seen` accepts `thread_ids`, `snooze` and `unsnooze` accept several threads, `reply` can forward a stored message with `forward_message_id`, `list` accepts `automated` and `include_archived`, and compose drafts carry `body_html`.
- `CampaignStep` exposes `thread_reply`, and `campaigns.create_step()` and `update_step()` accept it. `create_step()` now also takes the same optional fields as `update_step()` and applies them to the new step in one call; with no arguments it still creates a blank step.
- `Contacts.bulk_update`, `bulk_delete`, `request_verification` and `research_batch` accept a "select all matching" selection through `select_all`, `filters` and `exclude`, and id lists may now hold up to 10,000 contacts.
- `Contacts.update` can change a contact's `email`, `search` filters by `mail_hosts`, `lookup` accepts `thread_id` and `account_id` and reports `match`, and the contact models carry `mail_host`, `verification_requested_at`, `outreach`, `machine_opened_at`, the lead `sender_*`, `hold` and `cc` fields and the verification `verifier_*` fields.
- `GatewayEvent` gains the new realtime event names: `DIRECT_EMAIL_OPENED`, `DIRECT_EMAIL_CLICKED`, `WARMUP_PLACEMENT`, `MAILBOX_IMPORT_PROGRESS`, `CONTACT_IMPORT_PROGRESS`, `PLACEMENT_TEST_UPDATED` and `CRM_SYNCED`, each documented with the permission the server requires to receive it.
- `Meeting` gains `raw_payload`, the provider's original booking payload.
- `OAuthApplication` exposes `suspended_at` and `suspended_reason` for apps an operator has suspended.
- `OutreachSettings` exposes the `inbox_tagging` branch (hold on not now, stop on declined, call-request tasks, workspace tagging questions and languages).
- `Pipeline`, `Deal` and `CrmTask` gain `external`, the reference to the provider record when the workspace runs on a connected CRM, and `PipelineStage` gains `closed`, `won` and `probability`.
- `Plan` gains `price_yearly`, the yearly term price, and `None` marks a monthly-only plan.
- `advisor.list()` accepts `status` (one or more of open, snoozed, dismissed, applied, resolved) to list findings beyond the open ones.
- `campaigns.create()` and `campaigns.update()` accept `entry_delay_minutes` to hold a contact's first email back, and `Campaign` exposes it together with `effective_timezone`, the zone in use when the campaign follows the workspace timezone.
- `campaigns.estimate()` accepts `campaign_id`, `start_time`, `end_time` and `step_waits`, and `segment_ids` is now optional. `CampaignEstimate` also returns `steps`, `total_sends`, `first_touch_finish_at`, `steady_capacity`, `full_capacity_at`, `ramping`, `held`, `warmup`, `other_campaigns_per_day`, `bottleneck`, a day by day `timeline` and per mailbox `senders`.
- `campaigns.start()` accepts `acknowledge_list_risk` to launch past the bounce-risk gate, and `CampaignSegments` returns `withdrawn` and `contacted` after `set_segments()` detaches a segment.
- `crm.bulk_update_tasks()` and `crm.bulk_delete_tasks()` change or delete a selection of tasks, given as ids or as `select_all` with `filters` and `exclude`, and return the number affected.
- `emails.update()` now accepts `send_as_email`, `test_mode`, `test_send_enabled`, `test_receive_enabled`, `shared_daily_limit`, `rolling_recipient_limit`, `send_recovery_resolution`, `warmup_placement`, `warmup_folder`, `warmup_retention_days` and `relay_folder_moves`, and `EmailAccount` exposes the matching fields plus `auth_method`, `mail_host`, `vendor`, `avatar_url` and `track_direct_mail`.
- `integrations.clay_settings()` and `integrations.clay_update_settings()` read and edit a Clay connection's inbound defaults, outbound table and events.
- `integrations.community_apps()` and `integrations.community_app()` browse the community app directory, returning `CommunityApp` models.
- `integrations.push()` accepts `select_all`, `filters` and `exclude` to push every contact a search matches (up to 500) instead of listing ids, and `contact_ids` is now optional.
- `integrations.set_connection_signing_key()` and `integrations.rotate_inbound_url()` manage the signing key and the inbound webhook URL of Calendly and Cal.com connections. `IntegrationCatalogEntry` gains `rank`.
- `integrations` gains the Apollo calls: `apollo_overview()`, `apollo_replace_key()`, `apollo_lists()`, `apollo_preview_import()`, the `apollo_*_import_source` calls to list, create, update, run and delete saved list imports, and `apollo_enrichments()`, `apollo_start_enrichment()` and `apollo_enrichment()` for contact enrichment.
- `integrations` gains the Salesforce calls: `salesforce_overview()`, `get_salesforce_settings()` and `set_salesforce_settings()`, `salesforce_metadata()`, `salesforce_users()`, `salesforce_list_views()`, `salesforce_campaigns()`, `salesforce_preview_import()`, the `salesforce_*_import_source` calls, `salesforce_activity()`, `salesforce_retry_activity()` and `salesforce_sync_now()`.
- `oauth_applications` gains `set_logo` and `delete_logo` for an application's logo, and `retrieve_listing`, `put_listing` and `delete_listing` to manage its community directory listing. `OAuthApplication` now exposes `suspended_at` and `suspended_reason`.
- `segments.set_members()` now takes `select_all`, `filters` and `exclude` to override every contact matching a search instead of listing ids, and `contacts` is optional. `SegmentField` gains `option_labels`.

### Changed

- The `analytics` methods now send the query parameters the server actually reads: `dashboard()` takes `period`, `campaign_ids` and `folder_ids`, `usage()` takes `period`, `campaign_hourly()` takes `date`, `warmup()` takes `email_id`, `compare_campaigns()` takes `campaign_ids`, and `accounts()` takes `email_ids`, `limit` and `cursor` and returns a `pagination` block. Report dates are `YYYY-MM-DD` where the server reads days.
- The realtime gateway client now sends its API key, OAuth token or session token in the `X-Warmbly-Token` handshake header instead of the `token` query parameter, which the server deprecates for long-lived credentials because URLs are logged by proxies.
- The unibox models carry the newer server fields: `email_id` and `folder` on `Message`, `answers_mailbox_id` on `MessagePreview`, and `automated` and `automated_unread` on `UniboxOverview`. The `snoozed` filter documents the values the server reads (`true` and `any`) and `since` and `until` document the `YYYY-MM-DD` format.
- `EmailVerification` now matches what `emails.verify()` returns: `status`, `sub_status`, `reason`, `is_catch_all`, `has_mx`, `provider`, `confidence` and `checked_at`. The `valid`, `deliverable` and `catch_all` fields were never sent by the server and are gone.

### Deprecated

- The `from_` and `to` arguments of `analytics.dashboard()`, `usage()`, `campaign_hourly()`, `accounts()` and `account()` are deprecated: the server never read them for those reports, so use `period`, `date` or `email_ids` instead.

### Removed

- Removed the `description` argument of `teams.create()` and `teams.update()` and the `description` and `member_count` fields of `Team`. The server never stored or returned them, so the argument was silently ignored.
- Removed the campaign `kind` field: `campaigns.create()` no longer takes `kind`, `Campaign` no longer has `kind`, and `CampaignsOverview` no longer has `one_time`, because the server no longer has one-time campaigns.

### Fixed

- Rate limit errors now read the server's `retry_after_ms`, so `RateLimitError.retry_after` is exact for waits under a second, and `code` is set to `rate_limit_exceeded`. Error responses without an `X-Request-Id` header fall back to the `request_id` in the error body.
- `Contacts.create` and `Contacts.bulk_update` now return the bare list of `Contact` objects the server sends, instead of an empty `ContactsAdded`. A select-all edit, which the server answers with no rows, returns an empty list.
- `LeadSyncPreview` and `LeadSyncSpreadsheet` now match what the server returns. The preview carries `columns`, `sample_rows`, `has_header`, `suggested_mapping` and the other import preview fields instead of the never-populated `headers` and `rows`, and the spreadsheet id is `sheet_id` instead of `spreadsheet_id`.
- `automations.update()` now works for partial changes. The server replaces the whole definition on every write, so omitted fields are read from the stored automation first and sent back unchanged. Single automations are also decoded correctly: the server's `{"automation": {...}}` wrapper is lifted so `automation.id` and the other fields are populated.

### Documentation

- Documented that `warmup_routing.update()` replaces the whole rule on the server, and that `deliverability.ingest_event()` also accepts `open`, `click` and `reply` events.
- Resource docstrings for groups, teams, meetings, advisor, AI skills, AI tools and timezones now name the required scopes and the real response shapes (timezones carry `name` and `display_name`).


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

