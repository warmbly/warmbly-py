"""The ``migrations`` resource: bring data over from another outreach tool.

Maps to the ``/v1/migrations`` route group. A migration moves a workspace's
setup out of another cold-outreach tool (Instantly, Smartlead, lemlist,
Apollo and the others :meth:`Migrations.providers` lists) into Warmbly, read
through that tool's own API with a key you paste:

1. :meth:`Migrations.create` checks every key, records who it acts as, and
   starts a scan. The migration is ``scanning``.
2. When the scan finishes the migration is ``ready`` and its ``inventory``
   previews what each source workspace holds: mailboxes, campaigns, leads and
   the blocklist. Poll :meth:`Migrations.retrieve` until then.
3. :meth:`Migrations.start` picks what to bring over (the ``kinds``, and
   optionally which campaigns) and the migration is ``running``. Each source
   workspace becomes a ``target`` with its own progress and counts.
4. When it ends (``completed``, ``failed`` or ``canceled``) each target's
   ``followup`` lists what still needs a person: mailboxes to reconnect, notes
   on what did not carry over, and the draft campaigns created for review.
   :meth:`Migrations.link_senders` adds mailboxes connected since then to the
   drafts that named them.

The source tool is only ever read. Campaigns arrive as drafts and nothing is
sent until you launch them. The pasted keys are stored encrypted and wiped
once the migration finishes, is canceled or is deleted
(``credentials_held`` turns ``False``).

Permissions: every route needs the ``IMPORT_TOOLS`` API permission and a
member allowed to manage contacts. A key limited to particular mailboxes or
campaigns (or a restricted member) is refused, since a migration writes
across the whole workspace. Bringing ``campaigns`` over, and linking senders,
also needs ``WRITE_CAMPAIGNS`` plus the manage-campaigns member permission;
bringing ``mailboxes`` over needs ``WRITE_EMAILS`` plus manage-mailboxes.
Mailbox passwords returned by the source tool are only used for a migration
created from a signed-in dashboard session, so through an API key such
mailboxes land in ``followup.reconnect`` instead of connecting on their own.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGiven, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncMigrations",
    "Migration",
    "MigrationAccount",
    "MigrationCampaign",
    "MigrationCampaignSummary",
    "MigrationCounts",
    "MigrationDeleted",
    "MigrationFollowup",
    "MigrationInventory",
    "MigrationMailbox",
    "MigrationOptions",
    "MigrationProvider",
    "MigrationProviderField",
    "MigrationProviderList",
    "MigrationSourceWorkspace",
    "MigrationTarget",
    "MigrationWorkspaceInventory",
    "Migrations",
]


# -- providers -----------------------------------------------------------------


class MigrationProviderField(BaseModel):
    """One credential input a provider asks for.

    ``key`` is the name to use in the credential mapping passed to
    :meth:`Migrations.create`. ``secret`` marks a value to treat like a
    password; ``options``, when set, is the fixed set of accepted values.
    """

    key: str
    label: str | None = None
    help: str | None = None
    secret: bool | None = None
    optional: bool | None = None
    placeholder: str | None = None
    options: Sequence[str] = []


class MigrationProvider(BaseModel):
    """A tool a workspace can migrate from.

    ``kinds`` are the kinds of data its API can read (``mailboxes``,
    ``campaigns``, ``leads``, ``blocklist``). ``workspaces`` is ``True`` when
    one key can see several client workspaces, ``multi_key`` when the tool
    issues one key per workspace, and ``mailbox_secrets`` when its API returns
    mailbox passwords.
    """

    id: str
    label: str | None = None
    fields: Sequence[MigrationProviderField] = []
    key_help: str | None = None
    key_url: str | None = None
    kinds: Sequence[str] = []
    workspaces: bool | None = None
    multi_key: bool | None = None
    mailbox_secrets: bool | None = None
    notes: Sequence[str] = []


class MigrationProviderList(BaseModel):
    """Every tool a workspace can migrate from."""

    data: Sequence[MigrationProvider] = []


# -- the migration -------------------------------------------------------------


class MigrationAccount(BaseModel):
    """Who a pasted key acts as in the source tool."""

    name: str | None = None
    email: str | None = None
    plan: str | None = None


class MigrationSourceWorkspace(BaseModel):
    """One client account or workspace inside the source tool.

    ``id`` is empty for the account itself. ``key`` is the index of the
    credential set that reads it, when the tool issues a key per workspace.
    """

    id: str | None = None
    name: str | None = None
    key: int | None = None


class MigrationCampaignSummary(BaseModel):
    """One source campaign as the preview lists it.

    ``steps`` and ``leads`` are ``-1`` when the source API cannot give them
    cheaply.
    """

    id: str | None = None
    name: str | None = None
    status: str | None = None
    steps: int | None = None
    leads: int | None = None


class MigrationInventory(BaseModel):
    """What one source workspace holds. A count is ``-1`` when the source API
    cannot give it cheaply."""

    mailboxes: int | None = None
    campaigns: int | None = None
    leads: int | None = None
    blocklist: int | None = None
    campaign_summaries: Sequence[MigrationCampaignSummary] = []


class MigrationWorkspaceInventory(BaseModel):
    """One source workspace and what the scan found in it.

    ``error`` is set when the workspace could not be read; such a workspace is
    left out when the migration starts.
    """

    workspace: MigrationSourceWorkspace | None = None
    inventory: MigrationInventory | None = None
    error: str | None = None


class MigrationOptions(BaseModel):
    """The choices a migration was started with (see :meth:`Migrations.start`)."""

    kinds: Sequence[str] = []
    campaign_ids: Sequence[str] = []
    in_flight: str | None = None
    skip_finished: bool | None = None
    warmup: bool | None = None


class MigrationCounts(BaseModel):
    """What one target brought over."""

    blocklist_imported: int | None = None
    mailboxes_queued: int | None = None
    mailboxes_manual: int | None = None
    campaigns_created: int | None = None
    campaigns_skipped: int | None = None
    steps_created: int | None = None
    leads_read: int | None = None
    contacts_imported: int | None = None
    contacts_updated: int | None = None
    leads_enrolled: int | None = None
    leads_not_enrolled: int | None = None
    leads_suppressed: int | None = None
    leads_failed: int | None = None


class MigrationMailbox(BaseModel):
    """A mailbox its owner still has to connect.

    ``kind`` is how it signs in: ``google``, ``microsoft``, ``smtp_imap`` or
    ``unknown``.
    """

    email: str | None = None
    kind: str | None = None


class MigrationCampaign(BaseModel):
    """One draft campaign a migration created.

    ``missing_senders`` are source sender addresses with no mailbox in the
    workspace yet; :meth:`Migrations.link_senders` adds them once connected.
    """

    source_id: str | None = None
    campaign_id: str | None = None
    name: str | None = None
    missing_senders: Sequence[str] = []


class MigrationFollowup(BaseModel):
    """What a person still has to do after a target ran.

    ``reconnect`` are mailboxes that sign in with Google or Microsoft, or whose
    password the source does not return. ``notes`` are things that did not
    carry over, such as LinkedIn steps. ``campaigns`` are the draft campaigns
    created, for review before launch.
    """

    reconnect: Sequence[MigrationMailbox] = []
    notes: Sequence[str] = []
    campaigns: Sequence[MigrationCampaign] = []


class MigrationTarget(BaseModel):
    """One source workspace brought into one Warmbly workspace.

    ``status`` is ``pending``, ``running``, ``completed``, ``failed`` or
    ``canceled``. ``phase`` is the kind being imported now, empty before the
    first. ``category_id`` is the contact category every imported contact is
    filed under, and ``mailbox_import_id`` the mailbox import that connects
    mailboxes the source returned passwords for.
    """

    id: str
    migration_id: str | None = None
    workspace: MigrationSourceWorkspace | None = None
    organization_id: str | None = None
    organization_name: str | None = None
    status: str | None = None
    phase: str | None = None
    counts: MigrationCounts | None = None
    followup: MigrationFollowup | None = None
    error: str | None = None
    mailbox_import_id: str | None = None
    category_id: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    updated_at: str | None = None


class Migration(BaseModel):
    """One import from another outreach tool.

    ``status`` is ``scanning``, ``ready``, ``running``, ``completed``,
    ``failed`` or ``canceled``. ``accounts`` are who each pasted key acts as,
    in the order they were added; ``inventory`` is what the scan found, one
    entry per source workspace; ``options`` is set once started; ``targets``
    track each source workspace's progress. ``credentials_held`` turns
    ``False`` once the keys have been wiped.
    """

    id: str
    organization_id: str | None = None
    agency_id: str | None = None
    created_by_user_id: str | None = None
    provider: str | None = None
    label: str | None = None
    status: str | None = None
    accounts: Sequence[MigrationAccount] = []
    inventory: Sequence[MigrationWorkspaceInventory] = []
    options: MigrationOptions | None = None
    targets: Sequence[MigrationTarget] = []
    error: str | None = None
    credentials_held: bool | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class MigrationDeleted(BaseModel):
    """The result of deleting a migration (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


# -- request bodies ------------------------------------------------------------


def _create_body(
    provider: str,
    credentials: Sequence[Mapping[str, str]],
    label: NotGivenOr[str],
) -> dict[str, Any]:
    return drop_not_given(
        {
            "provider": provider,
            "label": label,
            "credentials": [dict(c) for c in credentials],
        }
    )


def _start_body(
    kinds: Sequence[str],
    campaign_ids: NotGivenOr[Sequence[str]],
    in_flight: NotGivenOr[str],
    skip_finished: NotGivenOr[bool],
    warmup: NotGivenOr[bool],
    targets: NotGivenOr[Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    options = drop_not_given(
        {
            "kinds": list(kinds),
            "campaign_ids": (
                NOT_GIVEN if isinstance(campaign_ids, NotGiven) else list(campaign_ids)
            ),
            "in_flight": in_flight,
            "skip_finished": skip_finished,
            "warmup": warmup,
        }
    )
    return drop_not_given(
        {
            "options": options,
            "targets": (
                NOT_GIVEN
                if isinstance(targets, NotGiven)
                else [dict(t) for t in targets]
            ),
        }
    )


class Migrations(SyncAPIResource):
    """Synchronous ``migrations`` resource."""

    def providers(
        self, *, options: RequestOptions | None = None
    ) -> MigrationProviderList:
        """List the tools a workspace can migrate from and the credentials
        each one asks for.

        Requires the ``IMPORT_TOOLS`` permission.
        """
        return self._get(
            "/migrations/providers", cast_to=MigrationProviderList, options=options
        )

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[Migration]:
        """List the workspace's migrations, newest first.

        Requires the ``IMPORT_TOOLS`` permission.

        Args:
            limit: Page size, 1 to 100 (default 20).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/migrations",
            model=Migration,
            query=drop_not_given({"limit": limit, "cursor": cursor}),
            options=options,
        )

    def create(
        self,
        *,
        provider: str,
        credentials: Sequence[Mapping[str, str]],
        label: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Migration:
        """Create a migration: check every key and start scanning the source.

        Answers ``201`` with the migration ``scanning``; poll
        :meth:`retrieve` until it is ``ready``. A rejected key answers ``422``
        and an unreachable tool ``503``. At most 5 migrations may be in progress
        per workspace at once (``409`` beyond that).

        Requires the ``IMPORT_TOOLS`` permission and a member allowed to
        manage contacts.

        Args:
            provider: The tool's ``id`` from :meth:`providers`.
            credentials: One mapping per key, keyed by the provider's field
                ``key`` values (usually ``{"api_key": ...}``). Most tools take
                exactly one; a ``multi_key`` tool takes one per workspace.
            label: A name for the migration. Omitted, the tool's name is used.
        """
        return self._post(
            "/migrations",
            cast_to=Migration,
            body=_create_body(provider, credentials, label),
            options=options,
        )

    def retrieve(
        self, migration_id: str, *, options: RequestOptions | None = None
    ) -> Migration:
        """Retrieve a migration with its preview, progress and follow-up.

        Requires the ``IMPORT_TOOLS`` permission.
        """
        return self._get(
            f"/migrations/{migration_id}", cast_to=Migration, options=options
        )

    def start(
        self,
        migration_id: str,
        *,
        kinds: Sequence[str],
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        in_flight: NotGivenOr[str] = NOT_GIVEN,
        skip_finished: NotGivenOr[bool] = NOT_GIVEN,
        warmup: NotGivenOr[bool] = NOT_GIVEN,
        targets: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Migration:
        """Start bringing data over from a ``ready`` migration.

        Every readable source workspace lands in this workspace. Starting a
        migration that is already running answers with it as it stands.

        Requires the ``IMPORT_TOOLS`` permission and a member allowed to
        manage contacts, plus ``WRITE_CAMPAIGNS`` and the manage-campaigns
        member permission when ``kinds`` includes ``campaigns``, and
        ``WRITE_EMAILS`` and the manage-mailboxes member permission when it
        includes ``mailboxes``.

        Args:
            migration_id: The migration to start.
            kinds: What to bring over, any of ``blocklist``, ``mailboxes``,
                ``campaigns`` and ``leads`` the provider supports. They are
                applied in that order, so nobody blocked in the old tool is
                enrolled by a later step.
            campaign_ids: Limit campaigns (and their leads) to these source
                campaign ids. Omitted, every campaign comes over.
            in_flight: What happens to a lead the old tool was part way
                through a sequence with: ``restart`` enrolls it from the first
                step, ``skip`` (the default) imports the contact without
                enrolling it.
            skip_finished: Leave out campaigns the source marks completed or
                archived.
            warmup: Start warmup on mailboxes that connect, unless the source
                said off.
            targets: Source workspaces to leave out, as
                ``{"workspace_id": ..., "key": ..., "skip": True}`` entries
                (``key`` is the credential index from the inventory). A
                workspace's own migration accepts only skip entries.
        """
        return self._post(
            f"/migrations/{migration_id}/start",
            cast_to=Migration,
            body=_start_body(
                kinds, campaign_ids, in_flight, skip_finished, warmup, targets
            ),
            options=options,
        )

    def cancel(
        self, migration_id: str, *, options: RequestOptions | None = None
    ) -> Migration:
        """Cancel a migration that has not finished (``scanning``, ``ready``
        or ``running``), wiping the keys it holds.

        What was already brought over stays. Requires the ``IMPORT_TOOLS``
        permission.
        """
        return self._post(
            f"/migrations/{migration_id}/cancel", cast_to=Migration, options=options
        )

    def link_senders(
        self, migration_id: str, *, options: RequestOptions | None = None
    ) -> Migration:
        """Add mailboxes connected since the migration ran to the draft
        campaigns that named them as senders.

        Running it again changes nothing more. Requires the ``IMPORT_TOOLS``
        and ``WRITE_CAMPAIGNS`` permissions.
        """
        return self._post(
            f"/migrations/{migration_id}/link-senders",
            cast_to=Migration,
            options=options,
        )

    def delete(
        self, migration_id: str, *, options: RequestOptions | None = None
    ) -> MigrationDeleted:
        """Dismiss a migration that is not running, wiping any keys it holds.

        What it brought over stays. A running migration answers ``409``:
        cancel it first. Requires the ``IMPORT_TOOLS`` permission.
        """
        return self._delete(
            f"/migrations/{migration_id}", cast_to=MigrationDeleted, options=options
        )


class AsyncMigrations(AsyncAPIResource):
    """Asynchronous ``migrations`` resource."""

    async def providers(
        self, *, options: RequestOptions | None = None
    ) -> MigrationProviderList:
        """List the tools a workspace can migrate from and the credentials
        each one asks for.

        Requires the ``IMPORT_TOOLS`` permission.
        """
        return await self._get(
            "/migrations/providers", cast_to=MigrationProviderList, options=options
        )

    def list(
        self,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        cursor: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[Migration]:
        """List the workspace's migrations, newest first.

        Requires the ``IMPORT_TOOLS`` permission.

        Args:
            limit: Page size, 1 to 100 (default 20).
            cursor: An opaque cursor from a previous page.
        """
        return self._get_api_list(
            "/migrations",
            model=Migration,
            query=drop_not_given({"limit": limit, "cursor": cursor}),
            options=options,
        )

    async def create(
        self,
        *,
        provider: str,
        credentials: Sequence[Mapping[str, str]],
        label: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Migration:
        """Create a migration: check every key and start scanning the source.

        Answers ``201`` with the migration ``scanning``; poll
        :meth:`retrieve` until it is ``ready``. A rejected key answers ``422``
        and an unreachable tool ``503``. At most 5 migrations may be in progress
        per workspace at once (``409`` beyond that).

        Requires the ``IMPORT_TOOLS`` permission and a member allowed to
        manage contacts.

        Args:
            provider: The tool's ``id`` from :meth:`providers`.
            credentials: One mapping per key, keyed by the provider's field
                ``key`` values (usually ``{"api_key": ...}``). Most tools take
                exactly one; a ``multi_key`` tool takes one per workspace.
            label: A name for the migration. Omitted, the tool's name is used.
        """
        return await self._post(
            "/migrations",
            cast_to=Migration,
            body=_create_body(provider, credentials, label),
            options=options,
        )

    async def retrieve(
        self, migration_id: str, *, options: RequestOptions | None = None
    ) -> Migration:
        """Retrieve a migration with its preview, progress and follow-up.

        Requires the ``IMPORT_TOOLS`` permission.
        """
        return await self._get(
            f"/migrations/{migration_id}", cast_to=Migration, options=options
        )

    async def start(
        self,
        migration_id: str,
        *,
        kinds: Sequence[str],
        campaign_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        in_flight: NotGivenOr[str] = NOT_GIVEN,
        skip_finished: NotGivenOr[bool] = NOT_GIVEN,
        warmup: NotGivenOr[bool] = NOT_GIVEN,
        targets: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Migration:
        """Start bringing data over from a ``ready`` migration.

        Every readable source workspace lands in this workspace. Starting a
        migration that is already running answers with it as it stands.

        Requires the ``IMPORT_TOOLS`` permission and a member allowed to
        manage contacts, plus ``WRITE_CAMPAIGNS`` and the manage-campaigns
        member permission when ``kinds`` includes ``campaigns``, and
        ``WRITE_EMAILS`` and the manage-mailboxes member permission when it
        includes ``mailboxes``.

        Args:
            migration_id: The migration to start.
            kinds: What to bring over, any of ``blocklist``, ``mailboxes``,
                ``campaigns`` and ``leads`` the provider supports. They are
                applied in that order, so nobody blocked in the old tool is
                enrolled by a later step.
            campaign_ids: Limit campaigns (and their leads) to these source
                campaign ids. Omitted, every campaign comes over.
            in_flight: What happens to a lead the old tool was part way
                through a sequence with: ``restart`` enrolls it from the first
                step, ``skip`` (the default) imports the contact without
                enrolling it.
            skip_finished: Leave out campaigns the source marks completed or
                archived.
            warmup: Start warmup on mailboxes that connect, unless the source
                said off.
            targets: Source workspaces to leave out, as
                ``{"workspace_id": ..., "key": ..., "skip": True}`` entries
                (``key`` is the credential index from the inventory). A
                workspace's own migration accepts only skip entries.
        """
        return await self._post(
            f"/migrations/{migration_id}/start",
            cast_to=Migration,
            body=_start_body(
                kinds, campaign_ids, in_flight, skip_finished, warmup, targets
            ),
            options=options,
        )

    async def cancel(
        self, migration_id: str, *, options: RequestOptions | None = None
    ) -> Migration:
        """Cancel a migration that has not finished (``scanning``, ``ready``
        or ``running``), wiping the keys it holds.

        What was already brought over stays. Requires the ``IMPORT_TOOLS``
        permission.
        """
        return await self._post(
            f"/migrations/{migration_id}/cancel", cast_to=Migration, options=options
        )

    async def link_senders(
        self, migration_id: str, *, options: RequestOptions | None = None
    ) -> Migration:
        """Add mailboxes connected since the migration ran to the draft
        campaigns that named them as senders.

        Running it again changes nothing more. Requires the ``IMPORT_TOOLS``
        and ``WRITE_CAMPAIGNS`` permissions.
        """
        return await self._post(
            f"/migrations/{migration_id}/link-senders",
            cast_to=Migration,
            options=options,
        )

    async def delete(
        self, migration_id: str, *, options: RequestOptions | None = None
    ) -> MigrationDeleted:
        """Dismiss a migration that is not running, wiping any keys it holds.

        What it brought over stays. A running migration answers ``409``:
        cancel it first. Requires the ``IMPORT_TOOLS`` permission.
        """
        return await self._delete(
            f"/migrations/{migration_id}", cast_to=MigrationDeleted, options=options
        )
