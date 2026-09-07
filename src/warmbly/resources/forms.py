"""The ``forms`` resource: hosted lead-capture forms.

Maps to the ``/v1/forms`` route group. A form is an ordered list of blocks plus
a design theme, published at a public URL and embeddable on any website. A
submission creates or updates a contact, files it under the form's categories,
and optionally adds it to a campaign.

Only a ``published`` form renders and accepts submissions; archiving keeps the
data but takes the page offline. ``share_url`` is the hosted page, built on the
organization's verified custom forms domain when it has one and on the
install's shared host otherwise.

Personalized links tie a submission back to the contact it came from:
:meth:`Forms.mint_link` returns the URL for one contact, and the campaign
editor's ``{{form_link:<public_id>}}`` marker mints them per recipient.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .._models import BaseModel
from .._pagination import AsyncPaginator, SyncCursorPage
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGivenOr, RequestOptions
from .._utils import drop_not_given

__all__ = [
    "AsyncForms",
    "CampaignFormStats",
    "Form",
    "FormDeleted",
    "FormLink",
    "FormStats",
    "FormStatsTotals",
    "FormSubmission",
    "FormSubmissionDeleted",
    "Forms",
    "FormsConfig",
    "FormsDomainStatus",
]


class Form(BaseModel):
    """A hosted lead-capture form.

    ``public_id`` is the unguessable token in the public URL and in embed
    codes; ``fields`` is the ordered block list, where the layout blocks
    (``heading``, ``paragraph``, ``divider``, ``page_break``) render but
    collect nothing. ``design`` is the theme the builder's Design panel edits.
    """

    id: str
    organization_id: str | None = None
    created_by: str | None = None
    public_id: str | None = None
    name: str | None = None
    status: str | None = None
    fields: Sequence[dict[str, Any]] = []
    design: dict[str, Any] | None = None
    success_message: str | None = None
    redirect_url: str | None = None
    campaign_id: str | None = None
    category_ids: Sequence[str] = []
    allowed_domains: Sequence[str] = []
    captcha_enabled: bool | None = None
    logo_url: str | None = None
    cover_url: str | None = None
    background_url: str | None = None
    views_count: int | None = None
    submissions_count: int | None = None
    starts_count: int | None = None
    identified_count: int | None = None
    trend: Sequence[int] = []
    last_submission_at: str | None = None
    published_at: str | None = None
    share_url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class FormDeleted(BaseModel):
    """The result of deleting a form (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class FormsConfig(BaseModel):
    """What this install can do, so a builder never offers an unusable toggle.

    ``captcha_available`` is ``False`` when no captcha provider is configured,
    in which case ``captcha_enabled`` on a form has no effect.
    """

    base_url: str | None = None
    captcha_available: bool | None = None


class FormsDomainStatus(BaseModel):
    """The organization's custom forms domain and its DNS verdict.

    ``cname_target`` is the value to point the CNAME at. ``status`` is stable
    and machine-readable: ``verified``, ``unset``, ``no_target``,
    ``not_found``, ``wrong_target`` or ``lookup_error``; ``observed`` is what
    DNS actually returned. Only a verified domain is used to build form URLs.
    """

    forms_domain: str | None = None
    forms_domain_verified: bool | None = None
    forms_domain_verified_at: str | None = None
    cname_target: str | None = None
    status: str | None = None
    message: str | None = None
    observed: str | None = None
    forms_host_unresolvable: bool | None = None


class FormSubmission(BaseModel):
    """One submission, kept verbatim.

    ``data`` is keyed by field id: a checkbox group stores a list of strings,
    every other block a single string. ``campaign_id`` names the campaign whose
    email carried the personalized link the visitor arrived through, if any.
    """

    id: str
    form_id: str | None = None
    organization_id: str | None = None
    contact_id: str | None = None
    campaign_id: str | None = None
    data: dict[str, Any] = {}
    source_url: str | None = None
    contact_email: str | None = None
    contact_name: str | None = None
    campaign_name: str | None = None
    created_at: str | None = None


class FormSubmissionDeleted(BaseModel):
    """The result of deleting a submission (``204 No Content``)."""

    id: str | None = None
    deleted: bool | None = None


class FormStatsTotals(BaseModel):
    """The funnel totals over the requested range."""

    views: int | None = None
    starts: int | None = None
    submissions: int | None = None
    completion_rate: float | None = None
    identified_visitors: int | None = None


class FormStats(BaseModel):
    """One form's analytics over a date range.

    ``pages`` is the per-page funnel (how many visitors reached each page and
    how many of those went on to submit); ``sources``, ``countries``,
    ``devices`` and ``campaigns`` are ``{"key", "count"}`` breakdowns;
    ``identified`` lists the visitors a contact could be put to.
    """

    totals: FormStatsTotals | None = None
    daily: Sequence[dict[str, Any]] = []
    pages: Sequence[dict[str, Any]] = []
    sources: Sequence[dict[str, Any]] = []
    countries: Sequence[dict[str, Any]] = []
    devices: Sequence[dict[str, Any]] = []
    campaigns: Sequence[dict[str, Any]] = []
    identified: Sequence[dict[str, Any]] = []


class FormLink(BaseModel):
    """A personalized form URL for one contact."""

    url: str | None = None


class CampaignFormStats(BaseModel):
    """How one form performed for a single campaign's recipients.

    ``links_sent`` is how many recipients were given a personalized link, and
    the rest is what they did with it.
    """

    form_id: str | None = None
    form_name: str | None = None
    public_id: str | None = None
    status: str | None = None
    links_sent: int | None = None
    viewers: int | None = None
    starters: int | None = None
    submissions: int | None = None
    share_url: str | None = None


def _form_body(
    *,
    name: NotGivenOr[str],
    status: NotGivenOr[str],
    fields: NotGivenOr[Sequence[Mapping[str, Any]]],
    design: NotGivenOr[Mapping[str, Any]],
    success_message: NotGivenOr[str],
    redirect_url: NotGivenOr[str],
    campaign_id: NotGivenOr[str | None],
    category_ids: NotGivenOr[Sequence[str]],
    allowed_domains: NotGivenOr[Sequence[str]],
    captcha_enabled: NotGivenOr[bool],
) -> dict[str, Any]:
    """Build the update body. Omitted fields keep their stored value."""
    return drop_not_given(
        {
            "name": name,
            "status": status,
            "fields": fields,
            "design": design,
            "success_message": success_message,
            "redirect_url": redirect_url,
            "campaign_id": campaign_id,
            "category_ids": category_ids,
            "allowed_domains": allowed_domains,
            "captcha_enabled": captcha_enabled,
        }
    )


class Forms(SyncAPIResource):
    """Synchronous ``forms`` resource."""

    def list(self, *, options: RequestOptions | None = None) -> SyncCursorPage[Form]:
        """List the organization's forms, with their funnel aggregates."""
        return self._get_api_list("/forms", model=Form, options=options)

    def config(self, *, options: RequestOptions | None = None) -> FormsConfig:
        """Report what this install supports (public base URL, captcha)."""
        return self._get("/forms/config", cast_to=FormsConfig, options=options)

    def create(self, *, name: str, options: RequestOptions | None = None) -> Form:
        """Create a draft form. Everything else is set with :meth:`update`."""
        return self._post("/forms", cast_to=Form, body={"name": name}, options=options)

    def retrieve(self, form_id: str, *, options: RequestOptions | None = None) -> Form:
        """Retrieve a single form by id."""
        return self._get(f"/forms/{form_id}", cast_to=Form, options=options)

    def update(
        self,
        form_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        fields: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        design: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        success_message: NotGivenOr[str] = NOT_GIVEN,
        redirect_url: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str | None] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        allowed_domains: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        captcha_enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Form:
        """Update a form. Omitted fields keep their stored value.

        Args:
            form_id: The form id.
            name: The internal name.
            status: ``draft``, ``published`` or ``archived``.
            fields: The ordered block list. Each block needs a slug ``id``, a
                ``type``, and a ``label`` unless it is a layout block; an input
                block may ``map_to`` a contact column (``first_name``,
                ``last_name``, ``email``, ``company``, ``phone``) instead of
                landing in the contact's custom fields.
            design: The theme (colors, fonts, layout, header, cover).
            success_message: Shown after a successful submit.
            redirect_url: Sent to instead of showing the success message.
            campaign_id: A campaign to add every new contact to; pass ``None``
                to detach.
            category_ids: Categories to file new contacts under.
            allowed_domains: Domains the form may be embedded on.
            captcha_enabled: Require a captcha, where the install has one.
        """
        return self._patch(
            f"/forms/{form_id}",
            cast_to=Form,
            body=_form_body(
                name=name,
                status=status,
                fields=fields,
                design=design,
                success_message=success_message,
                redirect_url=redirect_url,
                campaign_id=campaign_id,
                category_ids=category_ids,
                allowed_domains=allowed_domains,
                captcha_enabled=captcha_enabled,
            ),
            options=options,
        )

    def delete(
        self, form_id: str, *, options: RequestOptions | None = None
    ) -> FormDeleted:
        """Delete a form and its submissions."""
        return self._delete(f"/forms/{form_id}", cast_to=FormDeleted, options=options)

    # -- submissions ---------------------------------------------------------
    def list_submissions(
        self,
        form_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        before: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> SyncCursorPage[FormSubmission]:
        """List a form's submissions, newest first.

        Paged with a ``before`` timestamp (RFC 3339 nano); ``limit`` caps at
        100.
        """
        return self._get_api_list(
            f"/forms/{form_id}/submissions",
            model=FormSubmission,
            query={"limit": limit, "before": before},
            options=options,
        )

    def delete_submission(
        self,
        form_id: str,
        submission_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> FormSubmissionDeleted:
        """Delete one submission. The contact it created is untouched."""
        return self._delete(
            f"/forms/{form_id}/submissions/{submission_id}",
            cast_to=FormSubmissionDeleted,
            options=options,
        )

    # -- analytics + links ---------------------------------------------------
    def stats(
        self,
        form_id: str,
        *,
        range: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> FormStats:
        """Return the funnel, daily series, and breakdowns for a form.

        Args:
            form_id: The form id.
            range: ``"7d"``, ``"30d"`` (default) or ``"90d"``.
        """
        return self._get(
            f"/forms/{form_id}/stats",
            cast_to=FormStats,
            query=drop_not_given({"range": range}),
            options=options,
        )

    def mint_link(
        self, form_id: str, contact_id: str, *, options: RequestOptions | None = None
    ) -> FormLink:
        """Return the personalized form URL for one contact.

        The ticket is stable: minting again for the same contact hands back the
        same link.
        """
        return self._get(
            f"/forms/{form_id}/links/{contact_id}",
            cast_to=FormLink,
            options=options,
        )

    # -- brand assets --------------------------------------------------------
    def upload_asset(
        self,
        form_id: str,
        kind: str,
        *,
        file: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        options: RequestOptions | None = None,
    ) -> Form:
        """Upload a brand asset (multipart, PNG or JPG only).

        Args:
            form_id: The form id.
            kind: ``"logo"`` (max 1 MB, 1024px), ``"cover"`` or
                ``"background"`` (max 4 MB, 2560px).
            file: The raw image bytes.
            filename: The upload filename.
            content_type: The image's MIME type.
        """
        return self._client.request(
            cast_to=Form,
            method="POST",
            path=f"/forms/{form_id}/assets/{kind}",
            files={"file": (filename, file, content_type)},
            options=options,
        )

    def delete_asset(
        self, form_id: str, kind: str, *, options: RequestOptions | None = None
    ) -> Form:
        """Remove a brand asset, returning the form without it."""
        return self._delete(
            f"/forms/{form_id}/assets/{kind}", cast_to=Form, options=options
        )

    # -- custom domain -------------------------------------------------------
    def domain(self, *, options: RequestOptions | None = None) -> FormsDomainStatus:
        """Read the stored custom forms domain. Does no DNS work."""
        return self._get("/forms/domain", cast_to=FormsDomainStatus, options=options)

    def set_domain(
        self, *, forms_domain: str, options: RequestOptions | None = None
    ) -> FormsDomainStatus:
        """Set the custom forms domain and resolve it once.

        Args:
            forms_domain: The host to serve forms from, or ``""`` to clear it
                and fall back to the install's shared host.
        """
        return self._put(
            "/forms/domain",
            cast_to=FormsDomainStatus,
            body={"forms_domain": forms_domain},
            options=options,
        )

    def verify_domain(
        self, *, options: RequestOptions | None = None
    ) -> FormsDomainStatus:
        """Re-resolve the stored domain and persist the verdict."""
        return self._post(
            "/forms/domain/verify", cast_to=FormsDomainStatus, options=options
        )


class AsyncForms(AsyncAPIResource):
    """Asynchronous ``forms`` resource."""

    def list(self, *, options: RequestOptions | None = None) -> AsyncPaginator[Form]:
        """List the organization's forms, with their funnel aggregates."""
        return self._get_api_list("/forms", model=Form, options=options)

    async def config(self, *, options: RequestOptions | None = None) -> FormsConfig:
        """Report what this install supports (public base URL, captcha)."""
        return await self._get("/forms/config", cast_to=FormsConfig, options=options)

    async def create(self, *, name: str, options: RequestOptions | None = None) -> Form:
        """Create a draft form. Everything else is set with :meth:`update`."""
        return await self._post(
            "/forms", cast_to=Form, body={"name": name}, options=options
        )

    async def retrieve(
        self, form_id: str, *, options: RequestOptions | None = None
    ) -> Form:
        """Retrieve a single form by id."""
        return await self._get(f"/forms/{form_id}", cast_to=Form, options=options)

    async def update(
        self,
        form_id: str,
        *,
        name: NotGivenOr[str] = NOT_GIVEN,
        status: NotGivenOr[str] = NOT_GIVEN,
        fields: NotGivenOr[Sequence[Mapping[str, Any]]] = NOT_GIVEN,
        design: NotGivenOr[Mapping[str, Any]] = NOT_GIVEN,
        success_message: NotGivenOr[str] = NOT_GIVEN,
        redirect_url: NotGivenOr[str] = NOT_GIVEN,
        campaign_id: NotGivenOr[str | None] = NOT_GIVEN,
        category_ids: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        allowed_domains: NotGivenOr[Sequence[str]] = NOT_GIVEN,
        captcha_enabled: NotGivenOr[bool] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> Form:
        """Update a form. Omitted fields keep their stored value.

        Args:
            form_id: The form id.
            name: The internal name.
            status: ``draft``, ``published`` or ``archived``.
            fields: The ordered block list. Each block needs a slug ``id``, a
                ``type``, and a ``label`` unless it is a layout block; an input
                block may ``map_to`` a contact column (``first_name``,
                ``last_name``, ``email``, ``company``, ``phone``) instead of
                landing in the contact's custom fields.
            design: The theme (colors, fonts, layout, header, cover).
            success_message: Shown after a successful submit.
            redirect_url: Sent to instead of showing the success message.
            campaign_id: A campaign to add every new contact to; pass ``None``
                to detach.
            category_ids: Categories to file new contacts under.
            allowed_domains: Domains the form may be embedded on.
            captcha_enabled: Require a captcha, where the install has one.
        """
        return await self._patch(
            f"/forms/{form_id}",
            cast_to=Form,
            body=_form_body(
                name=name,
                status=status,
                fields=fields,
                design=design,
                success_message=success_message,
                redirect_url=redirect_url,
                campaign_id=campaign_id,
                category_ids=category_ids,
                allowed_domains=allowed_domains,
                captcha_enabled=captcha_enabled,
            ),
            options=options,
        )

    async def delete(
        self, form_id: str, *, options: RequestOptions | None = None
    ) -> FormDeleted:
        """Delete a form and its submissions."""
        return await self._delete(
            f"/forms/{form_id}", cast_to=FormDeleted, options=options
        )

    # -- submissions ---------------------------------------------------------
    def list_submissions(
        self,
        form_id: str,
        *,
        limit: NotGivenOr[int] = NOT_GIVEN,
        before: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> AsyncPaginator[FormSubmission]:
        """List a form's submissions, newest first.

        Paged with a ``before`` timestamp (RFC 3339 nano); ``limit`` caps at
        100.
        """
        return self._get_api_list(
            f"/forms/{form_id}/submissions",
            model=FormSubmission,
            query={"limit": limit, "before": before},
            options=options,
        )

    async def delete_submission(
        self,
        form_id: str,
        submission_id: str,
        *,
        options: RequestOptions | None = None,
    ) -> FormSubmissionDeleted:
        """Delete one submission. The contact it created is untouched."""
        return await self._delete(
            f"/forms/{form_id}/submissions/{submission_id}",
            cast_to=FormSubmissionDeleted,
            options=options,
        )

    # -- analytics + links ---------------------------------------------------
    async def stats(
        self,
        form_id: str,
        *,
        range: NotGivenOr[str] = NOT_GIVEN,
        options: RequestOptions | None = None,
    ) -> FormStats:
        """Return the funnel, daily series, and breakdowns for a form.

        Args:
            form_id: The form id.
            range: ``"7d"``, ``"30d"`` (default) or ``"90d"``.
        """
        return await self._get(
            f"/forms/{form_id}/stats",
            cast_to=FormStats,
            query=drop_not_given({"range": range}),
            options=options,
        )

    async def mint_link(
        self, form_id: str, contact_id: str, *, options: RequestOptions | None = None
    ) -> FormLink:
        """Return the personalized form URL for one contact.

        The ticket is stable: minting again for the same contact hands back the
        same link.
        """
        return await self._get(
            f"/forms/{form_id}/links/{contact_id}",
            cast_to=FormLink,
            options=options,
        )

    # -- brand assets --------------------------------------------------------
    async def upload_asset(
        self,
        form_id: str,
        kind: str,
        *,
        file: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        options: RequestOptions | None = None,
    ) -> Form:
        """Upload a brand asset (multipart, PNG or JPG only).

        Args:
            form_id: The form id.
            kind: ``"logo"`` (max 1 MB, 1024px), ``"cover"`` or
                ``"background"`` (max 4 MB, 2560px).
            file: The raw image bytes.
            filename: The upload filename.
            content_type: The image's MIME type.
        """
        return await self._client.request(
            cast_to=Form,
            method="POST",
            path=f"/forms/{form_id}/assets/{kind}",
            files={"file": (filename, file, content_type)},
            options=options,
        )

    async def delete_asset(
        self, form_id: str, kind: str, *, options: RequestOptions | None = None
    ) -> Form:
        """Remove a brand asset, returning the form without it."""
        return await self._delete(
            f"/forms/{form_id}/assets/{kind}", cast_to=Form, options=options
        )

    # -- custom domain -------------------------------------------------------
    async def domain(
        self, *, options: RequestOptions | None = None
    ) -> FormsDomainStatus:
        """Read the stored custom forms domain. Does no DNS work."""
        return await self._get(
            "/forms/domain", cast_to=FormsDomainStatus, options=options
        )

    async def set_domain(
        self, *, forms_domain: str, options: RequestOptions | None = None
    ) -> FormsDomainStatus:
        """Set the custom forms domain and resolve it once.

        Args:
            forms_domain: The host to serve forms from, or ``""`` to clear it
                and fall back to the install's shared host.
        """
        return await self._put(
            "/forms/domain",
            cast_to=FormsDomainStatus,
            body={"forms_domain": forms_domain},
            options=options,
        )

    async def verify_domain(
        self, *, options: RequestOptions | None = None
    ) -> FormsDomainStatus:
        """Re-resolve the stored domain and persist the verdict."""
        return await self._post(
            "/forms/domain/verify", cast_to=FormsDomainStatus, options=options
        )
