# Changelog

All notable changes to **warmbly-py** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this
project adheres to [Semantic Versioning](https://semver.org/). Entries are
assembled from news fragments in `changelog/` by
[towncrier](https://towncrier.readthedocs.io/) at release time.

<!-- towncrier release notes start -->

## [v0.4.0] - 2026-11-08

### Added

- Add `api_keys.delete_permanently` to remove a revoked or expired key and its usage logs.
- Add the `email_images` resource for the workspace image library used in email bodies: `list` (auto-paginating), a multipart `upload` and `delete`.
- Add `ErrorCode` and `ErrorReason` constants for the documented API error codes and an `APIError.reason` attribute. Add `APP_GRANTABLE_SCOPES` and `ROLE_PERMISSIONS` scope helpers, and a `deprecated` flag on webhook event types.
- Gateway: add event constants for `WARMUP_PLACEMENT`, `WARMUP_ACTIVITY`, `PLACEMENT_TEST_UPDATED`, `MAILBOX_IMPORT_PROGRESS`, `CONTACT_IMPORT_PROGRESS`, `CRM_SYNCED`, `DIRECT_EMAIL_OPENED` and `DIRECT_EMAIL_CLICKED`, plus `EVENT_PERMISSIONS`, `intent_matches` and `normalize_event_type`. `GatewayPushError` now exposes the structured `code` and `reason` of a refused join.
- Add the `leads` resource for the map-based lead finder: `config`, `geocode`, `search`, `query` (auto-paginating), `points`, `facets`, `retrieve`, `export`, single and bulk `update`, `update_many` and `delete_many`, website `enrich` runs with `list_enrichments` and `retrieve_enrichment`, `add_to_contacts`, saved searches (`list_searches`, `update_search`, `delete_search`) and the people on a lead (`add_person`, `update_person`, `delete_person`, `find_person_email`).
- Add `emails.identity` and `emails.refresh_identity` for a mailbox's send-as addresses, `emails.certificates` for an SMTP/IMAP mailbox's certificate policy, `emails.update_sync` for the folders a mailbox's sync skips, `emails.resume_sending` to lift a provider pause, `emails.update_direct_tracking`, and the `emails.bulk_delete`, `bulk_status` and `bulk_warmup` calls that answer a result per mailbox. Add `SendPauseInfo`, which types the `reason` of a mailbox pause (`rate_limited`, `daily_limit`, `sender_blocked`, `retry`, `domain_auth`, `permanent`, `authentication`).
- Add `oauth_applications.get_listing`, `put_listing` and `delete_listing` for an application's community directory listing, and `set_logo` and `remove_logo` to set an application's logo.
- Add `templates.analyze` for the AI spam analysis of template copy, returning typed findings, the rules score, the copy checker's judgment and what the call cost.
- Add `unibox.upsert_thread_draft` to hand in a reply you wrote for review, `unibox.move_folder` to file messages or conversations into inbox, archive or trash, and the `tag_ids`, `automated`, `include_archived`, `campaign_id` and `contact_id` filters on `unibox.list`. `UniboxOverview` gains `automated`, `automated_unread` and `drafts`, and `AgentDraft` now carries `owner_user_id`, `source_message_id`, `contact_id`, `campaign_id`, `to_addr`, `in_reply_to`, `intent_class`, `confidence` and `model`.
- Added `analytics.direct` for hand-written mail volume, replies and opt-in tracking, `analytics.inbox_tagging` (auto-paging) and `analytics.inbox_tagging_summary` for the automatic inbox-tagging review feed, and `analytics.warmup_placement` for where warmup mail landed.
- Added per-lead campaign controls: `campaigns.lead_cc`, `set_lead_cc` and `lead_cc_suggestions` for contacts copied on a lead's emails, and `lead_hold`, `pause_lead` and `resume_lead` to park one lead's flow. Added `campaigns.placement_monitor`, `put_placement_monitor` and `delete_placement_monitor` for a campaign's scheduled placement test, `campaigns.send_plan` for today's sending plan and every limit behind it, and `campaigns.warmup_placement`.
- Added the `placement` resource for inbox placement tests: `overview`, `coverage`, `list_tests`, `create_test`, `retrieve_test`, `cancel_test`, `list_seeds`, `set_seed`, and the many-sender batch methods `preview_batch`, `create_batch`, `list_batches`, `retrieve_batch`, `list_batch_senders` and `cancel_batch`, on both `Warmbly` and `AsyncWarmbly`. Create calls take `max_usd`, the most you agree to pay past the free allowance.
- Campaigns gained `follow_up_sender` (`same`, `same_domain` or `rotate`), `stop_on_meeting` and `entry_delay_minutes` on create, update and the `Campaign` model, plus `effective_timezone` on the model and `thread_reply` on steps. `campaigns.estimate` accepts `start_time`, `end_time`, `step_waits` and `campaign_id` (so `segment_ids` is now optional) and its result now carries the daily timeline, per-mailbox breakdown, bottleneck and finish-sooner scenarios.
- New `client.salesforce` (overview, settings, metadata, users, list views, campaigns, import sources and runs, activity log and retry, sync now) and `client.apollo` (overview, key replacement, lists, import sources and runs, enrichment runs) resources, plus Clay settings (`clay_settings`, `update_clay_settings`), the community app directory (`list_community_apps`, `retrieve_community_app`) and `rotate_inbound_url` / `set_signing_key` on `client.integrations`. Catalog entries gain `rank`.
- `client.contacts` gains background imports (`list_imports`, `create_import`, `retrieve_import`, `save_import_draft`, `analyze_import`, `start_import`, `cancel_import`, `import_failures`), the contact Salesforce panel (`salesforce`, `sync_salesforce`, `unlink_salesforce`), `lookup` by `thread_id` and `account_id` (the result now carries `match`), select-all selections (`select_all`, `filters`, `exclude`) on `bulk_update` and `bulk_delete`, an `email` argument on `update`, and a `mail_hosts` filter on `search`. Contacts gain `mail_host`, `outreach` and `verification_requested_at`; campaign states gain `sender_email`, `follow_up_sender`, `hold` and `cc`; sent emails gain `machine_opened_at`; timeline entries gain `bounce_cause`; import previews gain `column_stats`, `inferred_columns` and `mapping_source`.
- `client.crm` gains CRM mode for workspaces running on HubSpot or Pipedrive: `settings`, `update_settings`, `metadata`, `list_owners`, `map_owner`, `sync_health`, `sync_now`, `retry_sync_failures`, `discard_sync_failures`, `backfill_preview`, `start_backfill`, the provider-side contact record (`retrieve_contact`, `refresh_contact`, `link_contact`, `update_contact`), provider list import (`list_lists`, `preview_list_import`, `import_list`), and the bulk task actions `bulk_update_tasks` and `bulk_delete_tasks`. Pipelines, stages, deals, tasks and notes read in provider mode carry an `external` reference.

### Changed

- Gateway: API keys (`wmbly_`) and OAuth tokens (`wmat_`) are now sent in the `X-Warmbly-Token` handshake header instead of the URL, which the server now refuses. A refused handshake raises `FatalDisconnect` with the server's `code` and `reason`, and rate-limit or connection-cap refusals are retried.
- `EmailAccount` now carries `send_as_email`, `mail_host`, `auth_method`, `domain_grant_id`, `vendor_connection_id`, `vendor`, `avatar_url`, `last_id`, `test_mode`, `test_send_enabled`, `test_receive_enabled`, `shared_daily_limit`, `rolling_recipient_limit`, `track_direct_mail`, `warmup_placement`, `warmup_folder`, `warmup_retention_days` and `relay_folder_moves`, and `emails.update` accepts the editable ones plus `send_recovery_resolution`. `emails.sync` also reports `skip_folders` and the listed `folders`, `TrackingDomainStatus` gains `txt_name` and `txt_value`, and the `proof_missing` status is documented.

### Deprecated

- `kind` on campaigns and `one_time` on the campaigns overview are retired: current servers no longer return them and ignore `kind` on create. The parameters are kept so existing calls keep working.

### Security

- Debug request logs now redact `api_key`, `signing_key`, `auth_token` and `webhook_url` request fields.
- The inbound webhook URL on integration connections and the signing secret returned by `connection_webhook_secret` are now left out of the model `repr`, so printing or logging a response no longer exposes them.


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

