# Changelog

All notable changes to **warmbly-py** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this
project adheres to [Semantic Versioning](https://semver.org/). Entries are
assembled from news fragments in `changelog/` by
[towncrier](https://towncrier.readthedocs.io/) at release time.

<!-- towncrier release notes start -->

## [v0.4.0] - 2026-11-22

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
- Add the `reports` resource for client reports: list, create, retrieve, preview, update and delete a report, mint or revoke its public share link, and set or remove its email schedule.
- Added `ErrorCode` constants for the agency, agency key, Partnership mailbox connect, client connect link, client report, tool migration and cross-workspace copy refusals, plus `contact_limit_reached`, `scheduled_send_not_pending` and `idempotency_outcome_unknown`, the `409` a retried write gets when its first attempt's outcome is unknown.
- Added `campaigns.copy_to` and `templates.copy_to` to copy a campaign or reply templates into other workspaces as drafts, returning a per-workspace outcome, and `campaigns.lead_timezones` to count a campaign's leads by timezone before launch.
- Added `client.agency` for agency API keys: read the agency, its plans, staff, usage, AI balance, overview, brand, cross-client mailboxes and inbox, manage client workspaces and their caps, move AI balance to a client, and run migrations from other outreach tools into client workspaces.
- Added `client.migrations` to bring mailboxes, campaigns, leads and the blocklist over from another outreach tool: list the supported providers, create a migration with the source tool's key, preview the scan, start, cancel, link senders and delete it. Requires the new `IMPORT_TOOLS` API permission.
- Added the mailbox connect API to `emails`: Partnership plan workspaces can connect SMTP/IMAP and OAuth mailboxes (one at a time or in bulk), manage single-use sign-in links and their own OAuth apps. Also added client connect links (`create_client_link`, `list_client_links`, `list_client_link_uses`, `revoke_client_link`) and the per-mailbox warmup filter tag (`warmup_filter_tag`, `set_warmup_filter_tag`, `clear_warmup_filter_tag`).
- Agency API keys (`wmagency_`) work with both clients: pass `organization=` (or set `WARMBLY_ORGANIZATION`) to send the `Warmbly-Organization` header that names the client workspace an agency key acts in, and read `Identity.agency_id` from `client.me.retrieve()`. New scope constants `connect_emails`, `manage_reports` and `import_tools`, the agency-only `agency_read`, `agency_manage_clients`, `agency_read_usage`, `agency_transfer_ai` and `agency_migrate`, plus the `AGENCY_SCOPES`, `AGENCY_KEY_WORKSPACE_SCOPES` and `AGENCY_KEY_GRANTABLE_SCOPES` masks.
- Campaigns gained `timezone_mode` (`campaign` or `recipient`, to send on each lead's own clock) and `warmup_graduation` on create, update and the `Campaign` model. `campaigns.estimate` accepts `warmup_graduation` and the ramp schedule (`ramp_enabled`, `ramp_start`, `ramp_increment`, `ramp_ceiling`), and its `bottleneck` can now be `campaign_ramp`.
- Gateway: added the `EMAIL_BOUNCED` event constant, sent on `org:*` when a bounce or complaint is recorded against a campaign send. It needs `view_campaigns`.
- `leads.enrich` takes `web_search`, and enrichment runs report it; lead sites gain `read_via` and `unread`. Segment fields carry `option_labels` (the new `Location` fields are `world_region`, `country`, `timezone` and `location_known`). The forms domain status reports `txt_name`, `txt_value` and the `edge_records` still needed for HTTPS. Plans carry `price_yearly`, `monthly_allowance_usd`, `monthly_send_pool` and `agency_ai_allowance_usd`. Outreach settings carry `external_warmup`.
- Added the `store` resource to buy domains and Google Workspace or Microsoft 365 mailboxes and run them: `status`, `search_domains`, `set_registrant`, `create_quote`, `create_order` (pass `expected_due_now_micros` so a changed price is refused, not charged), `list_orders`, `retrieve_order`, domains (`list_domains`, `retrieve_domain`, `update_domain`, `renew_domain`, `transfer_out_domain`, `connect_domain` for a domain registered elsewhere, `check_domain_connection`, `regenerate_domain_connection`, `delete_domain`), DNS records (`create_dns_record`, `update_dns_record`, `delete_dns_record`, `check_dns`), `microsoft_consent`, mailboxes (`list_mailboxes`, `update_mailbox`, `set_mailbox_photo`, `cancel_mailbox`, `resume_mailbox`, `mailbox_sign_in`) and profile photos (`upload_photo`, `copy_profile_photo`, `retrieve_photo`). Reads need the new `READ_STORE` permission and changes need `MANAGE_STORE`; routes that charge also need the member's `manage_billing`. The transfer code and the mailbox password are kept out of `repr`.
- Added campaign review: `campaigns.review` for the readiness report (leads by review state, fields the emails print that leads have empty, AI copy written ahead), `set_review` to turn the approval hold on or off, `list_review_leads` (auto-paginating), `approve_review_leads`, `reopen_review_leads` and `write_review_ai` for paged AI write-ahead passes, plus per-lead copy with `lead_emails`, `personalize_lead_email`, `reset_lead_email` and `write_lead_email_ai`. `Campaign` gains `review_leads`, and a lead hold's `source` can be `review`.
- Added `agency.store_overview` for purchased domains and mailboxes across an agency's clients, and `emails.list_partner_mailboxes` for each mailbox's enablement in a workspace a partner manages.
- Apollo and Salesforce import sources and forms take `segment_ids` to pin every contact they bring in into chosen segments. Mailboxes carry `purchased` and `purchase_cancelled_at`, the mailbox sync policy reports `full_check_seconds`, and the agency AI top-up range reports the card processing fee as `fee_bps`.
- Added the `read_store` and `manage_store` scopes (bits 32 and 33, both delegated by `manage_emails`); the `READ_ONLY_SCOPES`, `FULL_ACCESS_SCOPES` and `ALL_SCOPES` masks include them as the server's presets do. Gateway: added `STORE_ORDER_UPDATED`, `STORE_DOMAIN_UPDATED` and `STORE_MAILBOX_UPDATED`, which need `manage_emails`.
- Added `ErrorCode` constants for the store refusals (`price_changed`, `payment_processing`, `plan_required`, `registrant_required`, `store_disabled`, `store_managed_by_partner`, `domain_unavailable`, `dns_record_conflict` and the rest), partner-managed workspaces (`organization_suspended`, `organization_cancelled`, `partner_managed_mailbox`), `purchased_mailbox`, `lead_step_sent`, and the AI spending refusals `ai_allowance_used` and `ai_overage_limit_reached`.

### Changed

- Gateway: API keys (`wmbly_`) and OAuth tokens (`wmat_`) are now sent in the `X-Warmbly-Token` handshake header instead of the URL, which the server now refuses. A refused handshake raises `FatalDisconnect` with the server's `code` and `reason`, and rate-limit or connection-cap refusals are retried.
- `EmailAccount` now carries `send_as_email`, `mail_host`, `auth_method`, `domain_grant_id`, `vendor_connection_id`, `vendor`, `avatar_url`, `last_id`, `test_mode`, `test_send_enabled`, `test_receive_enabled`, `shared_daily_limit`, `rolling_recipient_limit`, `track_direct_mail`, `warmup_placement`, `warmup_folder`, `warmup_retention_days` and `relay_folder_moves`, and `emails.update` accepts the editable ones plus `send_recovery_resolution`. `emails.sync` also reports `skip_folders` and the listed `folders`, `TrackingDomainStatus` gains `txt_name` and `txt_value`, and the `proof_missing` status is documented.
- `ALL_SCOPES` now means every workspace scope (it excludes the agency-only bits), `FULL_ACCESS_SCOPES` leaves out `connect_emails` as the server's preset does, and `APP_GRANTABLE_SCOPES` excludes `connect_emails` as well as `api_keys`.
- `forms.list_submissions` now follows the server's opaque cursor across pages and takes `cursor`; `before` applies to the first page only.

### Deprecated

- `kind` on campaigns and `one_time` on the campaigns overview are retired: current servers no longer return them and ignore `kind` on create. The parameters are kept so existing calls keep working.

### Fixed

- A `cursor` passed through `options={"query": ...}` on a list call no longer pins every page to the first one; auto-pagination now advances past it.
- A `409 idempotency_outcome_unknown` is raised at once instead of being retried with the same key, which could only get the same answer.
- Gateway `retry_after_ms` hints that are not positive finite numbers are ignored in favour of normal backoff, and `contacts.bulk_delete` now forwards `exclude` even without `select_all` or `filters`.

### Security

- Agency API keys (`wmagency_`) are scrubbed from debug logs like other Warmbly credentials.
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

