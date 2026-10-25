# Changelog

All notable changes to **warmbly-py** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this
project adheres to [Semantic Versioning](https://semver.org/). Entries are
assembled from news fragments in `changelog/` by
[towncrier](https://towncrier.readthedocs.io/) at release time.

<!-- towncrier release notes start -->

## [v0.4.0] - 2026-10-25

### Added

- Added `APP_GRANTABLE_SCOPES`, the mask of every scope a third-party OAuth app may request.
- Added `ErrorCode`, named constants for the machine-readable error `code`, an `APIError.reason` attribute for the optional finer `reason` key, and `ServiceUnavailableError.retry_after`.
- Added `GatewayEvent` constants for `WARMUP_PLACEMENT`, `PLACEMENT_TEST_UPDATED`, `MAILBOX_IMPORT_PROGRESS`, `CONTACT_IMPORT_PROGRESS`, `CRM_SYNCED`, `DIRECT_EMAIL_OPENED` and `DIRECT_EMAIL_CLICKED`.
- Added `analytics.direct` (hand-written mail volume, replies and opt-in tracking), `analytics.inbox_tagging` and `analytics.inbox_tagging_overview` (how replies were classified), and `analytics.warmup_placement` (where warmup mail landed per day and recipient provider), all returning typed models.
- Added `api_keys.delete_permanently` to remove a revoked or expired key for good.
- Added `campaigns.placement_monitor`, `set_placement_monitor` and `delete_placement_monitor` for a campaign's scheduled inbox placement test.
- Added `campaigns.send_plan` for today's sending plan of a campaign: what will go out, every limit that decided it, the sending window, the lead supply and each mailbox's day.
- Added `client.integrations.apollo` (overview, key replacement, lists, list import sources and enrichment runs through `start_enrichment`) and `client.integrations.clay` (`get_settings` and `update_settings` for inbound defaults and the outbound table).
- Added `client.integrations.salesforce`, the native Salesforce sync: `overview`, `get_settings` and `update_settings`, `metadata`, `list_users`, `list_views` and `list_campaigns`, `preview_import` and the saved import sources (`list_import_sources`, `create_import_source`, `update_import_source`, `run_import_source`, `delete_import_source`), and the activity log with `list_activity`, `retry_activity` and `sync_now`.
- Added `client.placement` for inbox placement testing: `overview`, `list_tests`, `retrieve_test`, `create_test`, `cancel_test`, `list_batches`, `retrieve_batch`, `list_batch_senders`, `preview_batch`, `create_batch`, `cancel_batch`, `coverage`, `seeds` and `set_seed`. A batch tests one message from many senders chosen by id or by a server-side scope, and results are typed down to each probe's folder and authentication evidence.
- Added `contacts.get_salesforce`, `sync_salesforce` and `unlink_salesforce` for a contact's linked Salesforce record, its opportunities and its sync state.
- Added `crm.bulk_update_tasks` and `crm.bulk_delete_tasks`, which write a status or priority onto, or delete, a list of tasks or every task matching a filter.
- Added `emails.direct_tracking`, `emails.update_sync`, `emails.certificates`, `emails.identity` and `emails.refresh_identity`: switch open and click tracking on hand-written sends, choose the IMAP folders the sync skips, read an SMTP/IMAP mailbox's certificate policy, and read or refresh the addresses a mailbox may send as. `emails.sync` now also reports `skip_folders` and the folders the sync has seen.
- Added `integrations.list_community_apps` and `get_community_app` for the community directory, `integrations.set_signing_key` and `rotate_inbound_url` for Calendly and Cal.com connections, and `rank` on `IntegrationCatalogEntry`. `integrations.bookings` needs the `read_contacts` permission, as the server now requires.
- Added `oauth_applications.upload_application_logo` and `delete_application_logo` for an app's own logo, and `get_listing`, `put_listing` and `delete_listing` to publish an app to the community directory.
- Added `price_yearly` to `Plan`, the price the yearly term charges (`None` when the plan is monthly only).
- Added `templates.analyze` for an AI spam analysis of template content that locates each problem in the subject or body, suggests a rewrite and reports the credits it spent.
- Added `thread_reply` to `CampaignStep` and to `campaigns.update_step`, which sends a follow-up as a reply in the first email's conversation. `campaigns.create_step` now accepts the same fields as `update_step` and applies them to the new step in one call. Campaigns gain `entry_delay_minutes` on create and update and an `effective_timezone` on read.
- Added `unibox.move_folder` to archive, delete or restore messages and whole conversations, `unibox.reply(forward_message_id=...)` to forward a stored message, `thread_ids` on `unibox.mark_seen`, `unibox.snooze_many` and `unibox.unsnooze_many`, the `automated` and `include_archived` list filters, and the `automated` counts on `UniboxOverview`.
- Added per-lead controls on a campaign: `campaigns.lead_hold`, `pause_lead` and `resume_lead` park one contact's flow without unsubscribing them, and `lead_cc`, `set_lead_cc` and `lead_cc_suggestions` manage the colleagues copied on every email to a lead.
- Added staged contact imports: `contacts.create_import` uploads a file as a draft, `save_import_draft`, `analyze_import` and `start_import` map and run it in the background, `retrieve_import` and `list_imports` follow it, `cancel_import` stops it and `download_import_failures` returns every failed row as CSV. `ContactImportPreview` now carries `inferred_columns`, `column_stats` and `mapping_source`, and `ContactImportResult` carries `segments_pinned`.
- Added submission triage to forms: `triage_enabled` on `forms.update`, `triage` and `triage_confidence` on `FormSubmission`, `redirect_url_active` on `Form` and `triage_available` on `FormsConfig`.
- Added the `inbox_tagging` branch to `OutreachSettings`, which controls what a classified reply may do, and documented that `outreach.update_settings` fills fields left out of the document with the server defaults.
- Added the connected-CRM routes of `client.crm` (HubSpot and Pipedrive): `get_settings` and `update_settings`, `metadata`, `list_owners` and `map_owner`, `sync_health`, `sync_now`, `retry_sync_failures` and `discard_sync_failures`, `backfill_preview` and `start_backfill`, `get_contact`, `refresh_contact`, `link_contact` and `update_contact`, and `list_lists`, `preview_list_import` and `import_list` to turn a CRM list into a staged contact import. Pipelines, stages, deals and tasks carry `external` when they live in the connected CRM.
- Added the workspace email image library: `campaigns.list_email_images`, `upload_email_image` and `delete_email_image`.
- Bulk contact actions now accept a "select all matching" selection through `select_all`, `filters` and `exclude`: `contacts.bulk_update`, `contacts.bulk_delete`, `contacts.request_verification`, `contacts.research_batch`, `integrations.push` and the Apollo enrichment. Explicit id lists may now hold up to 10000 contacts, and the id argument of each is optional.
- Lead sync sources can pin every synced row into segments: `segment_ids` on `lead_sync.create_source`, `update_source` and `LeadSyncSource`, and `lead_sync.list_sources(segment_id=...)` filters by segment.
- `emails.update` now accepts `send_as_email`, `test_mode`, `test_send_enabled`, `test_receive_enabled`, `shared_daily_limit`, `rolling_recipient_limit`, `send_recovery_resolution`, `warmup_placement`, `warmup_folder`, `warmup_retention_days` and `relay_folder_moves`, and `EmailAccount` carries the matching fields along with `mail_host`, `auth_method`, `domain_grant_id`, `vendor`, `vendor_connection_id`, `avatar_url`, `last_id` and `track_direct_mail`.
- `segments.set_members` now accepts a "select all matching" selection through `all`, `filters` and `exclude`, and `contacts` is optional. `SegmentField` exposes `option_labels`.

### Changed

- A `503` with code `ai_not_configured` is no longer retried, since it means the deployment has no AI provider. Other `503` responses are still retried, honoring `Retry-After`.
- The realtime gateway client now sends API keys and OAuth tokens in the `X-Warmbly-Token` handshake header instead of the URL, as the gateway requires, and reads the gateway's `{code, reason}` refusal body: `FatalDisconnect` carries `code` and `reason`, and rate-limit and connection-cap refusals are retried after the hinted delay.
- `Contact` now reads `mail_host`, `verification_requested_at` and `outreach`, `ContactSentEmail` reads `machine_opened_at`, and `ContactCampaignState` reads `sender_id`, `sender_email`, `hold` and `cc`. `contacts.search` filters by `mail_hosts` and sorts by a custom field with `custom:<key>`. `contacts.update` can change a contact's `email`. `contacts.lookup` resolves a reply from an alias address through `thread_id` and `account_id`, and `ContactLookup.match` says how it matched. `ContactVerificationRequested` reports the `verifier` that runs a queued check, and `ContactNote` carries `external` for notes that live in a connected CRM.
- `OAuthApplication` now reports `suspended_at` and `suspended_reason`, and `oauth_applications.developer_access` reports whether the workspace may register and publish apps. The `oauth_applications.update` documentation now says the server replaces the whole registration, so send `name`, `redirect_uris` and `scopes` every time.
- `TemplateScore.issues` is now a list of typed `TemplateIssue` objects with `severity`, `code`, `message`, `field`, `spans` and `suggestion`, matching what the server sends. The `grade` and `suggestions` attributes are removed because the server never returned them.
- `api_keys.permissions` now reports `grantable`, the permission mask the caller may put on a key, and `app_scopes`, the mask an OAuth app may request. Key and app management routes are documented as unavailable to OAuth app tokens.
- `campaigns.estimate` now returns the day-by-day projection (`timeline`, `senders`, `steps`, `total_sends`, `steady_capacity`, `bottleneck` and related fields) and accepts `start_time`, `end_time`, `step_waits` and `campaign_id`. `segment_ids` is now optional so a saved campaign can be projected from its own leads. `campaigns.set_segments` reports `withdrawn` and `contacted` for the leads a detached segment removed.

### Removed

- Removed the `description` argument of `teams.create` and `teams.update` and the `description` and `member_count` attributes of `Team`, which the server does not support: a description was accepted and silently dropped.
- Removed the `from_` and `to` arguments of `analytics.dashboard`, `analytics.usage`, `analytics.campaign_hourly` and `analytics.account`, which the API ignores. `analytics.warmup` and `analytics.campaign_daily` now require `from_` and `to`, and `analytics.compare_campaigns` requires `ids`, `from_` and `to`, because the API rejects a request without them.
- Removed the one-time campaign kind, which the server retired: `kind` is gone from `campaigns.create`, from `Campaign` and the `one_time` count is gone from `CampaignsOverview`.

### Fixed

- Analytics methods now send the query parameters the API reads. `analytics.dashboard` takes `period`, `campaign_ids` and `folder_ids`, `analytics.usage` takes `period`, `analytics.campaign_hourly` takes `date`, `analytics.compare_campaigns` takes `ids`, `analytics.warmup` takes `email_id`, and `analytics.accounts` takes `email_ids`, `limit` and `cursor`. Date windows are whole days (`YYYY-MM-DD`) except for `analytics.deliverability`, which still takes RFC 3339 timestamps.
- Corrected the documented values of the `unibox.list` filters: `since` and `until` take a `YYYY-MM-DD` date, and `snoozed` takes `"true"` or `"any"`.
- `ApiKeyUsageAnalytics.from_` now reads the `from` field the API sends; it was always `None`.
- `LeadSyncPreview` now reads the fields the server sends (`columns`, `sample_rows`, `has_header`, `total_rows`, `suggested_mapping`, `inferred_columns`, `mapping_source`) and `LeadSyncSpreadsheet` reads `sheet_id`. The `headers` and `rows` attributes of the preview and `spreadsheet_id` are removed because the server never returned them.

### Documentation

- Documented the `entity_type` values the audit trail now writes, including `campaign_lead`, `mailbox_import`, `email_image`, `app_listing`, `oauth_application` and the placement entities.
- Documented the permissions behind `advisor.apply` and `advisor.undo`, the mailbox-limit and confirmation errors of `ai_tools`, the key-holder rule for `ai_skills` writes and the `action_provider_mismatch` error of `automations`.


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

