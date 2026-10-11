# Changelog

All notable changes to **warmbly-py** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this
project adheres to [Semantic Versioning](https://semver.org/). Entries are
assembled from news fragments in `changelog/` by
[towncrier](https://towncrier.readthedocs.io/) at release time.

<!-- towncrier release notes start -->

## [v0.4.0] - 2026-10-11

### Added

- Add `analytics.direct()` for hand-written mail volume and tracking, `analytics.inbox_tagging()` for reviewing automatic inbox-tagging verdicts, and `analytics.warmup_placement()` for where warmup mail landed per day and recipient provider.
- Add the `placement` resource (`client.placement` and `async_client.placement`) for inbox placement tests: `overview`, `list_tests`, `get_test`, `create_test`, `cancel_test`, `list_batches`, `get_batch`, `list_batch_senders`, `preview_batch`, `create_batch`, `cancel_batch`, `coverage`, `list_seeds` and `set_seed`. List methods auto-page, and the responses of this group are unwrapped from their `{"data": ...}` envelope.
- Added `ErrorCode`, constants for the machine-readable `code` values in API error responses (for example `ErrorCode.REAUTH_REQUIRED` and `ErrorCode.PASSWORD_BREACHED`), and `APIError.requires_reauth`, which is true when the server wants a recent re-authentication at `POST /auth/reauth` before a sensitive account change.
- Added `api_keys.delete_permanently()` to remove a revoked or expired API key and its usage logs.
- Added `emails.identity()` and `emails.refresh_identity()` for a mailbox's send-as addresses and signature source, `emails.update_sync()` to choose folders the sync skips, and `emails.update_direct_tracking()` for open and click tracking on direct unibox sends. `emails.sync()` now also returns `skip_folders`, the server's `folders`, and the skipped-folder counts.
- Added `unibox.move_folder()` to archive, trash or restore messages and whole conversations. `unibox.mark_seen()` accepts `thread_ids`, `unibox.reply()` accepts `forward_message_id` to forward a stored message, and `unibox.list()` accepts `include_archived` and `automated`. Message, preview and overview models gain `email_id`, `folder`, `answers_mailbox_id`, `automated` and `automated_unread`.
- Added the `GatewayEvent` constants `WARMUP_PLACEMENT`, `PLACEMENT_TEST_UPDATED`, `MAILBOX_IMPORT_PROGRESS`, `CONTACT_IMPORT_PROGRESS`, `DIRECT_EMAIL_OPENED` and `DIRECT_EMAIL_CLICKED`. Each documents its payload fields and the member permission the server requires to receive it.
- Background contact imports: `contacts.create_import()`, `list_imports()`, `retrieve_import()`, `save_import_draft()`, `analyze_import()`, `start_import()`, `cancel_import()` and `download_import_failures()` upload a file once, preview and analyze a column mapping over the whole file, run the import in the background and fetch the failed rows as CSV.
- New `email_images` resource (`list()`, `upload()`, `delete()`) for the workspace image library used in email bodies. Uploads are multipart and return a public `url` ready to place in a campaign or template.
- Per-lead controls on a campaign: `campaigns.lead_hold()`, `pause_lead()` and `resume_lead()` park one contact's flow without unsubscribing them, and `lead_cc()`, `set_lead_cc()` and `suggest_lead_cc()` manage the colleagues copied on every email to a lead. `ContactCampaignState` now carries `sender_id`, `sender_email`, `hold` and `cc`, and a lead can have the `paused` status.
- `campaigns.placement_monitor()`, `set_placement_monitor()` and `delete_placement_monitor()` read, create or update, and remove a campaign's scheduled inbox-placement test (`PlacementMonitor`: interval, panel, alert threshold, pause on alert).
- `campaigns.send_plan()` returns today's sending plan for a campaign as a `CampaignSendPlan`: the configured ceiling, every limit that reduced it, the sending window, lead supply, each mailbox's day and the workspace allowance.
- `crm.bulk_update_tasks()` and `crm.bulk_delete_tasks()` change the status or priority of, or delete, a whole selection of tasks by id or by "select all matching" filter, and report how many were affected.
- `integrations.set_connection_signing_key()` sets (or clears) the key a Calendly or Cal.com connection's deliveries must be signed with, and `rotate_connection_inbound_url()` mints a new inbound webhook URL for it.
- `templates.analyze()` runs the AI spam analysis on template copy and returns located findings, a suggested subject and the rules score as a `TemplateAnalysis`. It spends AI credits.
- Added `APP_GRANTABLE_SCOPES`, the mask an OAuth app may request (every scope except `api_keys`), and the `grantable` and `app_scopes` masks on the result of `api_keys.permissions()`.
- Added `ErrorCode` constants for the codes the server introduced for member access scopes, credential management, the CRM and Salesforce integrations, the OAuth app directory, Cloud connection refusals, Slack linking, recipient validation and re-authentication limits (for example `MEMBER_ACCESS_RESTRICTED`, `API_KEY_PERMISSIONS_EXCEED_CALLER`, `OAUTH_TOKEN_NOT_ALLOWED`, `CRM_REAUTH_REQUIRED`, `SALESFORCE_RECONNECT_REQUIRED`, `INVALID_RECIPIENT` and `REAUTH_LIMITED`), and `APIError.access_restricted`, true when a selected-resource access scope refused the request.
- Added the `GatewayEvent.CRM_SYNCED` constant for the realtime event sent when mirrored CRM records change (a connected CRM pushed or pulled). The payload carries `org_id`, `objects` and, when one contact is affected, `contact_id`; it has no permission gate, but members restricted to selected resources never receive it.
- Placement results gain `first_folder`, `observed_at`, `late_observation` and `evidence` (the receiver authentication headers and DKIM verification), and placement counts gain `unknown`, `archive`, `custom`, `observed_receipts`, `classified_receipts`, `unresolved`, `primary_metric` and `non_spam_metric`, each metric carrying its numerator, denominator and 95 percent interval. A result `folder` can now also be `unknown`, `archive` or `custom`.
- `analytics.dashboard()` accepts `campaign_ids` and `folder_ids` to narrow the campaign sections to chosen campaigns and campaign folders; the response echoes a `scope`. Analytics responses also carry positive reply counts and rates, `interested_leads` and `reply_breakdown`.
- `client.salesforce` covers the native Salesforce sync under `/integrations/salesforce/{id}`: the health overview, sync settings, org metadata, users, list views and campaigns, saved imports with preview and run, the activity log with retry, and sync now.
- `contacts.salesforce()`, `contacts.sync_salesforce()` and `contacts.unlink_salesforce()` read a contact's Salesforce panel, push it to Salesforce, and drop a record link.
- `crm` can now run and inspect a workspace on a connected HubSpot or Pipedrive CRM: `get_settings()` and `update_settings()` read and switch the CRM mode, `get_metadata()` and `list_owners()` feed the pickers, `map_owner()` pins a provider owner to a member, `get_sync_health()`, `sync_now()`, `retry_sync_failures()` and `discard_sync_failures()` manage the sync outbox, `get_backfill_preview()` and `start_backfill()` copy Warmbly's own deals, tasks and notes across, `retrieve_contact()`, `refresh_contact()`, `link_contact()` and `update_contact()` work with a contact's provider record, and `list_lists()`, `preview_list_import()` and `import_list()` turn a provider list into a contact import draft. Retrying or discarding with an empty `ids` list raises `ValueError` instead of widening to every failed job.
- `emails.update()` accepts `test_mode`, `test_send_enabled`, `test_receive_enabled`, `shared_daily_limit`, `rolling_recipient_limit` and `send_recovery_resolution` (release a send hold with evidence), and `EmailAccount` carries the same participation and limit fields. New mailboxes default to diagnostic participation off.
- `integrations.community()` and `integrations.get_community_app()` browse the community app directory, listed apps for discovery and any published app by its link slug.
- `oauth_applications.set_logo()` uploads a logo onto an existing application and `remove_logo()` clears it, both returning the updated `OAuthApplication`. `retrieve_listing()`, `put_listing()` and `delete_listing()` read, publish or replace, and unpublish the application's community directory listing (`OAuthAppListing`).

### Changed

- Add `price_yearly` to the `Plan` model. It is `None` for a plan that is monthly only.
- Align the `analytics` methods with the query parameters the server reads: `dashboard` and `usage` take `period`, `warmup` takes `email_id`, `compare_campaigns` takes `ids`, `campaign_hourly` takes `date`, and `accounts` is now paged with `email_ids`, `limit` and `cursor`. The `from_` and `to` dates are whole days (`YYYY-MM-DD`), not RFC3339 timestamps. The existing arguments still work.
- Forms gain `triage_enabled`, `FormsConfig.triage_available` and the `triage` verdict on submissions. `SegmentField` reports `option_labels`. Lead sync sources carry `segment_ids`, accept it on create and update, and `lead_sync.list_sources()` can filter by `segment_id`.
- `EmailAccount` now carries `send_as_email`, `mail_host`, `auth_method`, `domain_grant_id`, `vendor_connection_id`, `vendor`, `avatar_url`, `track_direct_mail`, `warmup_placement`, `warmup_folder`, `warmup_retention_days` and `relay_folder_moves`, and `emails.update()` accepts `send_as_email`, `relay_folder_moves`, `warmup_placement`, `warmup_folder` and `warmup_retention_days`.
- `campaigns.create()` and `update()` accept `entry_delay_minutes`, `Campaign` reports it and `effective_timezone`, and `create_step()` can now take the step fields (including the new `thread_reply`) in the same call. `campaigns.estimate()` accepts `start_time`, `end_time`, `step_waits` and `campaign_id` and its result reports steps, total sends, steady capacity, the bottleneck, a day by day timeline and the sender pool. `set_segments()` reports `withdrawn` and `contacted`. One-time campaigns were retired by the server, so `kind` and `CampaignsOverview.one_time` are no longer returned; the `kind` argument is still accepted and ignored.
- `contacts.bulk_update()`, `bulk_delete()`, `request_verification()` and `research_batch()`, `integrations.push()` and `segments.set_members()` accept a "select all matching" selection (`select_all`, `filters`, `exclude`) in place of an id list, and the id limit per request is now 10000. `contacts.lookup()` takes `thread_id` and `account_id` as well as `email` and reports how it matched (`match`). `contacts.update()` can change `email`, `contacts.search()` filters by `mail_hosts`, and `Contact` reports `mail_host` and `verification_requested_at`.
- `unibox.snooze()` and `unibox.unsnooze()` now take either `thread_id` or `thread_ids`. `snooze()` no longer requires `thread_id`, and a multi-thread snooze returns its rows under `data`; calling either without a thread id raises `ValueError`.
- The gateway client now sends API keys (`wmbly_...`) and OAuth access tokens (`wmat_...`) in the `X-Warmbly-Token` handshake header instead of the `token` query parameter, which the server deprecates because URLs end up in proxy logs. The short-lived connection ticket still goes in the query string. No call-site change is needed.
- `OAuthApplication` reports `suspended_at` and `suspended_reason` when an instance operator suspended the app. The `oauth_applications` docstrings now say that OAuth app tokens are refused on these routes (`403`, `oauth_token_not_allowed`), that a suspended app answers `409` (`app_suspended`), and that secret rotation asks a dashboard session, never an API key, to re-confirm the account holder (`reauth_required`).

### Documentation

- Documented that a browser session connects to the gateway with the short-lived ticket from `POST /getaway`. The server now refuses any other session token with close code 4004, which the gateway client treats as fatal and does not retry.
- Documented newer server behavior: `analytics.warmup()` rejects a non-UUID `email_id` and a reversed range with a 400, `emails.update()` validates the warmup window as a pair, `tasks.replay()` refuses send-capable dead letters with a 409 and the `resolved` dead-letter status, campaign `daily_limit` is a per-mailbox ceiling from 3 to 5000, and send plans report the `send_recovery`, `send_cooldown` and `send_authority` states.
- The realtime guide now explains how the org channel filters events for members restricted to selected resources, and the 30-second authorization refresh.

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

