# Changelog

All notable changes to **warmbly-py** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this
project adheres to [Semantic Versioning](https://semver.org/). Entries are
assembled from news fragments in `changelog/` by
[towncrier](https://towncrier.readthedocs.io/) at release time.

<!-- towncrier release notes start -->

## [v0.4.0] - 2026-11-01

### Added

- `api_keys.delete_permanent()` removes a revoked or expired API key and its usage logs for good. `ApiKeyPermissions` gains `grantable`, the permission bitmask the caller may put on a key, and `app_scopes`, the bitmask an OAuth application may be granted.
- `contacts.bulk_update()`, `bulk_delete()` and `request_verification()` can act on every contact matching a search (`select_all=True` with `filters` and `exclude`) instead of an id list, and the id list is now optional. `contacts.update()` can change a contact's `email`, and `contacts.search()` accepts `mail_hosts`. `Contact` gains `mail_host`, `verification_requested_at` and `outreach`, `ContactSentEmail` gains `machine_opened_at`, and `ContactVerificationRequested` gains `verifier`, `verifier_label` and `verifier_error`.
- Background contact imports: `contacts.create_import()` uploads a file once and returns a draft with the preview the column mapper needs, `save_import_draft()` autosaves the mapping, `analyze_import()` reports what the draft would do across the whole file without writing anything, `start_import()` runs it in the background, `cancel_import()` stops it, and `list_imports()` (auto-paging), `retrieve_import()` and `download_import_failures()` follow it. `ContactImportPreview` gains `inferred_columns`, `column_stats` and `mapping_source`, and `ContactImportResult` gains `segments_pinned`, with `quality` now a typed `ContactImportQuality`.
- Salesforce on a contact: `contacts.salesforce()` returns the contact panel (connected orgs, linked Lead or Contact records, opportunities, tasks and sync state), `sync_salesforce()` matches or creates the record and pushes the contact, and `unlink_salesforce()` drops a link.
- Added `crm.bulk_update_tasks()` and `crm.bulk_delete_tasks()`, which act on a list of task ids or on a select-all (`select_all=True` with the search `filters` and `exclude`, up to 50,000 tasks) and return how many tasks were touched.
- Added the connected-CRM calls to `client.crm` for workspaces that run their CRM on HubSpot or Pipedrive: `get_settings()` and `update_settings()`, `get_metadata()`, `list_owners()` and `map_owner()`, `get_sync_health()`, `sync_now()`, `retry_sync_failures()` and `discard_sync_failures()`, `get_backfill()` and `start_backfill()`, `get_contact()`, `refresh_contact()`, `link_contact()` and `update_contact()`, and `list_lists()` (auto-paginating), `preview_import()` and `import_list()` for importing a provider list. Pipelines, deals and tasks gain `external` (`CrmExternalRef`), and pipeline stages gain `closed`, `won` and `probability`.
- New `email_images` resource for the workspace image library used in email bodies: `list()` (auto-paging), `upload()` and `delete()`, on both the sync and async clients.
- New mailbox methods: `emails.certificates()` reads an SMTP/IMAP mailbox's certificate policy per server, `send_identity()` and `refresh_send_identity()` read and refresh the addresses a mailbox may send as (optionally importing the provider signature), `update_direct_tracking()` switches open and click tracking on hand-written unibox sends, and `update_sync()` replaces the folders a mailbox's sync leaves alone. `MailboxSync` now carries `skip_folders` and `folders`.
- Added provider sub-namespaces on `client.integrations`. `apollo` covers the overview, key replacement, saved lists, import preview, import sources (list, create, update, run, delete) and enrichment runs (list, get, start). `salesforce` covers the overview, sync settings, field metadata, users, list views, campaigns, import preview, import sources, the activity log with retry, and sync-now. `clay` reads and updates the inbound defaults and the outbound table. Responses decode `null` lists as empty and keep unknown fields.
- Added `integrations.list_community_apps()` (auto-paginating) and `integrations.get_community_app()` to browse the community app directory, `integrations.rotate_inbound_url()` to mint a new inbound URL for a Calendly or Cal.com connection, and `integrations.set_signing_key()` to require signed deliveries on one. `IntegrationCatalogEntry` gains `rank`.
- OAuth application directory listings and logos: `oauth_applications.get_listing()`, `put_listing()` and `delete_listing()` manage an application's community directory page, and `set_logo()` and `delete_logo()` upload or remove its logo on the application itself. `OAuthApplication` gains `suspended_at` and `suspended_reason`.
- `templates.analyze()` runs an AI spam analysis on template content and names the word or sentence at fault, where it sits, and what to write instead. It charges AI credits and returns the rules score and a recipient-side judgment alongside the findings. `TemplateScore` no longer declares the `grade` and `suggestions` attributes, which the server never sent.
- `unibox.move_folder()` files messages and whole conversations into `inbox`, `archive` or `trash` (Move to inbox, Archive and Delete in the dashboard).
- Added `APP_GRANTABLE_SCOPES`, the mask of every scope an OAuth app can be granted (all except `api_keys`), and a `request_id` attribute on `OAuthError` for `server_error` responses from the token endpoint. The OAuth guide now explains that a token's granted scopes can be narrower than the ones requested because the approving member's role caps them, and that reusing an already exchanged refresh token revokes the grant.
- Added `warmbly.ErrorCode`, named constants for the machine-readable `code` values the API documents, and a `reason` attribute on `APIError` for the optional finer key some error codes carry. Unknown codes and reasons are still delivered as plain strings.
- Added gateway event constants for the event families the realtime service gained: `WARMUP_PLACEMENT`, `PLACEMENT_TEST_UPDATED`, `MAILBOX_IMPORT_PROGRESS`, `CONTACT_IMPORT_PROGRESS`, `CRM_SYNCED`, `DIRECT_EMAIL_OPENED` and `DIRECT_EMAIL_CLICKED`. The realtime guide now lists which read scope delivers which event family to an API key or OAuth token. Unknown event names continue to reach `on_event` handlers and `wait_for` unchanged.
- Forms gain submission triage: `forms.update()` takes `triage_enabled`, `Form` exposes `triage_enabled` and `redirect_url_active`, `FormSubmission` exposes `triage` and `triage_confidence`, `FormsConfig` exposes `triage_available`, and `FormsDomainStatus` exposes the `txt_name` and `txt_value` ownership record and the `proof_missing` status.
- Lead sync sources can pin every synced row into segments: `create_source()` and `update_source()` take `segment_ids`, `LeadSyncSource` exposes `segment_ids`, and `list_sources()` can filter with `segment_id`.
- New `client.placement` resource for inbox placement tests: `overview()`, `coverage()`, `list_seeds()` and `set_seed()` for the workspace's own seed inboxes, `list_tests()`, `retrieve_test()`, `create_test()` and `cancel_test()`, and `list_batches()`, `retrieve_batch()`, `list_batch_senders()`, `preview_batch()`, `create_batch()` and `cancel_batch()` to run one test from many senders. The list methods page automatically on both the sync and async clients. Single-object results keep the server's `data` envelope, so read them from `.data`.
- Per-lead controls on a campaign: `campaigns.get_lead_hold()`, `pause_lead()` and `resume_lead()` park one contact's flow without unsubscribing them, and `get_lead_cc()`, `set_lead_cc()` and `suggest_lead_cc()` manage the contacts copied on every email to one lead.
- Unibox: `list()` takes `automated` (only or without conversations no person wrote in) and `include_archived`; `mark_seen()` takes `thread_ids` to mark whole conversations; `reply()` takes `forward_message_id` to send a forward; the new `snooze_many()` snoozes several threads in one call and `unsnooze()` accepts `thread_ids`. `Message` gains `email_id` and `folder`, `MessagePreview` gains `answers_mailbox_id`, `SeenResult` gains `thread_ids` and `folder`, and `UniboxOverview` gains `automated`, `automated_unread` and `drafts`.
- `Plan` exposes `price_yearly`, and `OutreachSettings` exposes the `inbox_tagging` branch (the actions a classified reply may take).
- `analytics.direct()` reports hand-written mail volume, replies and opt-in tracking, `analytics.inbox_tagging()` and `list_inbox_tagging()` expose the automatic inbox-tagging review, and `analytics.warmup_placement()` reports where warmup mail landed per day and per recipient provider. `analytics.list_accounts()` pages through account statuses.
- `campaigns.get_placement_monitor()`, `set_placement_monitor()` and `delete_placement_monitor()` manage a campaign's scheduled placement test (interval, panel, alert threshold, pause on alert). `campaigns.send_plan()` reads today's sending plan with the limits that decided it.
- `segments.set_members()` can name its contacts as a select-all (`all=True` with `filters` and `exclude`) instead of an id list, and `contacts` is now optional. `SegmentField` gains `option_labels`, the display names of an enum field's values.

### Changed

- `contacts.lookup()` no longer requires `email`: it also accepts `thread_id` (resolving a reply that came from an alias to the lead the campaign wrote to) and `account_id`. `ContactLookup` gains `match`, which is `email` or `thread`.
- `emails.update()` accepts `send_as_email`, the placement-test participation settings (`test_mode`, `test_send_enabled`, `test_receive_enabled`, `shared_daily_limit`, `rolling_recipient_limit`), `send_recovery_resolution`, `warmup_placement`, `warmup_folder`, `warmup_retention_days` and `relay_folder_moves`, and `EmailAccount` gains the matching fields plus `mail_host`, `auth_method`, `avatar_url` and `track_direct_mail`. `TrackingDomainStatus` gains `txt_name` and `txt_value` and the `proof_missing` status. `EmailAuthCheck` now reads the fields the server sends (`domain`, `spf_found`, `spf_record`, `dkim_found`, `dkim_status`, `dmarc_found`, `dmarc_policy`, `dmarc_domain`, `dmarc_inherited`, `summary` and so on); the former `auth_state`, `spf`, `dkim`, `dmarc`, `reason` and `checked_at` attributes were never sent and are gone.
- `integrations.push()` can now name its contacts as a select-all (`select_all=True` with `filters` and `exclude`) or with `contacts`, and `contact_ids` is now optional. One push still takes at most 500 contacts.
- Documented behaviour the server changed on existing routes: advisor `apply()` and `undo()` run as the calling credential and honour a key's mailbox limit; `ai_tools.list()` and `call()` are refused for a key limited to specific mailboxes and for a member role without the AI assistant, and a fix that needs a fresh confirmation answers with the `reauth_required` code; `generation.edit()` limits count characters; `generation.ai_variable()` with a `contact_id` also needs the contacts read scope; folders, tags and categories belong to the organization rather than to their creator; an omitted field in `outreach.update_settings()` takes its default; automation writes refuse an action that does not run on its integration with the `action_provider_mismatch` code.
- `analytics` methods now send the query parameters the API reads. `dashboard()` takes `period`, `campaign_ids` and `folder_ids`; `warmup()` takes `email_id`; `compare_campaigns()` takes `ids`; `campaign_hourly()` takes `date`; `usage()` takes `period`; and `accounts()` takes `email_ids`, `limit` and `cursor` and returns `pagination`. The date range on `warmup()`, `compare_campaigns()`, `campaign()` and `campaign_daily()` is a day (`YYYY-MM-DD`), and `campaign()` now honors it. `from_` and `to` on `dashboard()` are ignored by the API.
- `campaigns.create()` and `update()` accept `entry_delay_minutes`, which holds a contact's first email back after they enter the campaign, and `Campaign` gains `entry_delay_minutes` and `effective_timezone`. `campaigns.update_step()` accepts `thread_reply` and `CampaignStep` gains it. `campaigns.estimate()` takes `start_time`, `end_time`, `step_waits` and `campaign_id`, makes `segment_ids` optional, and `CampaignEstimate` gains the day-by-day timeline, per-sender projection, steady capacity, warmup load, bottleneck and scenarios.

### Removed

- Breaking: removed `description` from `teams.create()` and `teams.update()` and `description` and `member_count` from `Team`. The API has no such fields, so the value was never stored and the attributes were always `None`.
- Breaking: removed `kind` from `campaigns.create()` and from `Campaign`, and `one_time` from `CampaignsOverview`. One-time campaigns were retired in the API, which no longer reads `kind` on create or returns it.

### Fixed

- The realtime gateway client now sends API keys and OAuth access tokens in the `X-Warmbly-Token` handshake header, which the gateway requires, instead of the URL query string, where it now refuses them. A short-lived connection JWT still goes in the query string. A refused handshake now reports the server's code and reason on `FatalDisconnect` (for example `Access token revoked`), and a handshake refused for rate limiting or the connection cap is retried after the server's `retry_after_ms` instead of ending the client.


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

