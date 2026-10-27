"""MCP tools for browser-backed Campaign Wizard campaigns."""

import os
from typing import cast

from server.contract import PUBLIC_CONTRACT
from server.main import mcp
from server.tools import ToolError, get_browser_runner, handle_cli_errors
from server.tools.browser_helpers import browser_session_args
from server.tools.helpers import (
    CliOption,
    _find_unsafe_json_integer,
    append_cli_options,
    check_batch_limit,
    expand_grouped_dicts,
    finalize_json_args,
    normalize_json_arg,
    require_non_empty_csv,
    require_update_fields,
    tool_error_dict,
    validate_enum,
)

MASTERS_STATUS_CHOICES = (
    "not-archived",
    "active",
    "stopped",
    "archived",
    "all",
)

MASTERS_LIST_OPTIONS = (
    CliOption("status", "--status"),
    CliOption("capture_timeout_seconds", "--timeout"),
)
MASTERS_GET_OPTIONS = (
    CliOption("moderation_statuses", "--moderation-statuses", is_flag=True),
    CliOption("tracking_params", "--tracking-params", is_flag=True),
)

# Families of flat params are exposed to the model as nested dict params (#298,
# pattern of #220-A/B) to shrink the JSON Schema; expand_grouped_dicts unfolds
# the dict keys back into the flat option names below before append_cli_options
# runs, so the generated `direct` argv stays byte-for-byte identical to a flat
# signature. Dict keys = the original flat param names.
MASTERS_ADD_DICT_REGISTRY: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("region_options", ("regions", "region_ids")),
)

MASTERS_UPDATE_DICT_REGISTRY: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "budget_options",
        ("weekly_budget", "promotion_goal", "goal_price", "directs_helps"),
    ),
    (
        "goal_options",
        ("target_action_prices", "add_target_actions", "remove_target_actions"),
    ),
    (
        "creative_options",
        (
            "name",
            "landing_url",
            "tracking_params",
            "headlines",
            "texts",
            "clear_headlines",
            "clear_texts",
        ),
    ),
    ("media_options", ("images", "add_video", "add_video_url", "remove_videos")),
    (
        "audience_options",
        (
            "gender",
            "age_from",
            "age_to",
            "devices",
            "add_audience_tags",
            "remove_audience_tags",
        ),
    ),
    (
        "metrika_options",
        (
            "add_metrika_counters",
            "remove_metrika_counters",
            "add_sitelinks",
            "remove_sitelinks",
        ),
    ),
    ("batch_options", ("moderation_statuses", "pacing_ms", "no_progress")),
)

MASTERS_ADD_OPTIONS = (
    CliOption("headlines", "--headline", repeat=True),
    CliOption("texts", "--text", repeat=True),
    CliOption("add_target_actions", "--add-target-action", repeat=True),
    CliOption("weekly_budget", "--weekly-budget"),
    CliOption("regions", "--region", repeat=True),
    CliOption("region_ids", "--region-id", repeat=True),
    CliOption("draft", "--draft", is_flag=True),
)

MASTERS_UPDATE_OPTIONS = (
    # budget_options
    CliOption("weekly_budget", "--weekly-budget"),
    CliOption("promotion_goal", "--promotion-goal"),
    CliOption("goal_price", "--goal-price"),
    # directs_helps is a tri-state --directs-helps/--no-directs-helps pair the
    # shared CliOption table cannot express; it is emitted right after these
    # options (see masters_update).
    # goal_options
    CliOption("target_action_prices", "--target-action-price", repeat=True),
    CliOption("add_target_actions", "--add-target-action", repeat=True),
    CliOption("remove_target_actions", "--remove-target-action", repeat=True),
    # creative_options
    CliOption("name", "--name"),
    CliOption("landing_url", "--landing-url"),
    CliOption("tracking_params", "--tracking-params"),
    CliOption("headlines", "--headline", repeat=True),
    CliOption("texts", "--text", repeat=True),
    CliOption("clear_headlines", "--clear-headline", repeat=True),
    CliOption("clear_texts", "--clear-text", repeat=True),
    # media_options
    CliOption("images", "--image", repeat=True),
    CliOption("add_video", "--add-video"),
    CliOption("add_video_url", "--add-video-url"),
    CliOption("remove_videos", "--remove-video", repeat=True),
    # audience_options
    CliOption("gender", "--gender"),
    CliOption("age_from", "--age-from"),
    CliOption("age_to", "--age-to"),
    CliOption("devices", "--device", repeat=True),
    CliOption("add_audience_tags", "--add-audience-tag", repeat=True),
    CliOption("remove_audience_tags", "--remove-audience-tag", repeat=True),
    # metrika_options (also owns the "Быстрые ссылки" sitelinks — see tool docs)
    CliOption("add_metrika_counters", "--add-metrika-counter", repeat=True),
    CliOption("remove_metrika_counters", "--remove-metrika-counter", repeat=True),
    CliOption("add_sitelinks", "--add-sitelink", repeat=True),
    CliOption("remove_sitelinks", "--remove-sitelink", repeat=True),
    # batch_options
    CliOption("moderation_statuses", "--moderation-statuses", is_flag=True),
    CliOption("pacing_ms", "--pacing-ms"),
    CliOption("no_progress", "--no-progress", is_flag=True),
    # launch stays a flat signature param on purpose (#298): publishing a draft
    # must not hide inside a dict, same reasoning as dry_run.
    CliOption("launch", "--launch", is_flag=True),
)

_PROMOTION_GOAL_CHOICES = ("max-clicks", "max-conversions")
_GENDER_CHOICES = ("any", "female", "male")
_AGE_FROM_CHOICES = ("0", "18", "25", "35", "45", "55")
_AGE_TO_CHOICES = ("18", "25", "35", "45", "55", "unlimited")
_DEVICE_CHOICES = ("mobile", "desktop", "tablet")

_UPDATE_ENUM_GUARDS = (
    ("promotion_goal", _PROMOTION_GOAL_CHOICES),
    ("gender", _GENDER_CHOICES),
    ("age_from", _AGE_FROM_CHOICES),
    ("age_to", _AGE_TO_CHOICES),
)

_CONTRACT_BY_NAME = {tool.public_name: tool for tool in PUBLIC_CONTRACT}


def _command_path(tool_name: str) -> list[str]:
    """Return the full direct CLI path declared by the public contract."""
    tool = _CONTRACT_BY_NAME[tool_name]
    if tool.cli_subcommand_path is not None:
        return list(tool.cli_subcommand_path)
    if tool.cli_service is None or tool.cli_subcommand is None:
        raise RuntimeError(f"{tool_name} has no direct CLI command path")
    return [tool.cli_service, tool.cli_subcommand]


def _run_browser_json(
    args: list[str], *, allow_nonzero: bool = False
) -> list[dict] | dict:
    args.extend(browser_session_args(os.environ))
    finalize_json_args(args, False)
    runner = get_browser_runner()
    if allow_nonzero:
        return runner.run_json_lenient(args, allow_nonzero=True)
    return runner.run_json_lenient(args)


@mcp.tool(
    name="masters_list",
    description="Read Campaign Wizard campaigns by status. See tool_help('masters_list').",
)
@handle_cli_errors
def masters_list(
    status: str = "not-archived",
    capture_timeout_seconds: int | None = None,
) -> list[dict] | dict:
    """List Campaign Wizard campaigns from the logged-in browser account.

    Args:
        status: Status filter: not-archived, active, stopped, archived, or all.
        capture_timeout_seconds: Seconds to wait for the grid's data request
            per capture attempt (two attempts are made — this budget, then
            double it — before the command fails). Raise on slow connections;
            the CLI validates the range.
    """
    enum_error = validate_enum(
        status,
        MASTERS_STATUS_CHOICES,
        field="status",
        error="invalid_status",
    )
    if enum_error:
        return tool_error_dict(enum_error)

    args = _command_path("masters_list")
    append_cli_options(args, locals(), MASTERS_LIST_OPTIONS)
    return _run_browser_json(args)


@mcp.tool(
    name="masters_get",
    description="Read Campaign Wizard campaigns by ID. See tool_help('masters_get').",
)
@handle_cli_errors
def masters_get(
    campaign_ids: str,
    moderation_statuses: bool = False,
    tracking_params: bool = False,
) -> list[dict] | dict:
    """Get one or more Campaign Wizard campaigns by comma-separated ID.

    ``tracking_params=True`` requires a direct-cli release containing commit
    https://github.com/axisrow/direct-cli/commit/4ce5b27. The published 0.5.2
    wheel predates that read flag; the default call remains compatible with it.

    Args:
        campaign_ids: Comma-separated campaign IDs.
        moderation_statuses: Include per-image moderation rejection details.
        tracking_params: Include UTM and URL tracking parameters.
    """
    normalized_ids = require_non_empty_csv(
        campaign_ids,
        error="missing_campaign_ids",
        noun="campaign ID",
    )
    if isinstance(normalized_ids, ToolError):
        return tool_error_dict(normalized_ids)

    args = [*_command_path("masters_get"), normalized_ids]
    append_cli_options(args, locals(), MASTERS_GET_OPTIONS)
    return _run_browser_json(args)


def _run_campaign_batch(tool_name: str, campaign_ids: str) -> list[dict] | dict:
    """Run one native browser session for a comma-separated campaign batch."""
    normalized_ids = require_non_empty_csv(
        campaign_ids,
        error="missing_campaign_ids",
        noun="campaign ID",
    )
    if isinstance(normalized_ids, ToolError):
        return tool_error_dict(normalized_ids)

    batch_error = check_batch_limit(normalized_ids)
    if batch_error:
        return tool_error_dict(batch_error)

    return _run_browser_json(
        [*_command_path(tool_name), normalized_ids], allow_nonzero=True
    )


@mcp.tool(
    name="masters_launch",
    description="Launch Wizard campaigns. See tool_help('masters_launch').",
)
@handle_cli_errors
def masters_launch(campaign_ids: str) -> list[dict] | dict:
    """Launch one or more draft campaigns by comma-separated ID.

    Args:
        campaign_ids: Comma-separated campaign IDs (maximum 10).
    """
    return _run_campaign_batch("masters_launch", campaign_ids)


@mcp.tool(
    name="masters_suspend",
    description="Suspend Wizard campaigns. See tool_help('masters_suspend').",
)
@handle_cli_errors
def masters_suspend(campaign_ids: str) -> list[dict] | dict:
    """Suspend one or more campaigns by comma-separated ID.

    Args:
        campaign_ids: Comma-separated campaign IDs (maximum 10).
    """
    return _run_campaign_batch("masters_suspend", campaign_ids)


@mcp.tool(
    name="masters_resume",
    description="Resume Wizard campaigns. See tool_help('masters_resume').",
)
@handle_cli_errors
def masters_resume(campaign_ids: str) -> list[dict] | dict:
    """Resume one or more campaigns by comma-separated ID.

    Args:
        campaign_ids: Comma-separated campaign IDs (maximum 10).
    """
    return _run_campaign_batch("masters_resume", campaign_ids)


@mcp.tool(
    name="masters_archive",
    description="Archive Wizard campaigns. See tool_help('masters_archive').",
)
@handle_cli_errors
def masters_archive(campaign_ids: str) -> list[dict] | dict:
    """Archive one or more campaigns by comma-separated ID.

    Args:
        campaign_ids: Comma-separated campaign IDs (maximum 10).
    """
    return _run_campaign_batch("masters_archive", campaign_ids)


@mcp.tool(
    name="masters_copy",
    description="Copy a Wizard campaign. See tool_help('masters_copy').",
)
@handle_cli_errors
def masters_copy(campaign_id: str) -> dict:
    """Clone a campaign and save the copy as a draft.

    Args:
        campaign_id: Source campaign ID.
    """
    args = [*_command_path("masters_copy"), str(campaign_id)]
    return cast(dict, _run_browser_json(args))


def _get_campaign_resource(tool_name: str, campaign_id: str) -> dict:
    # Keep object IDs as strings at the MCP boundary: JavaScript hosts can round
    # int64 values before Python sees them. Click still validates this token as INT.
    return cast(
        dict,
        _run_browser_json([*_command_path(tool_name), str(campaign_id)]),
    )


@mcp.tool(
    name="masters_adimages_get",
    description="Read Campaign Wizard images. See tool_help('masters_adimages_get').",
)
@handle_cli_errors
def masters_adimages_get(campaign_id: str) -> dict:
    """Get the campaign's current image set.

    Args:
        campaign_id: Campaign ID.
    """
    return _get_campaign_resource("masters_adimages_get", campaign_id)


@mcp.tool(
    name="masters_targetactions_get",
    description="Read Campaign Wizard goals. See tool_help('masters_targetactions_get').",
)
@handle_cli_errors
def masters_targetactions_get(campaign_id: str) -> dict:
    """Get the campaign's target-action goals and prices.

    Args:
        campaign_id: Campaign ID.
    """
    return _get_campaign_resource("masters_targetactions_get", campaign_id)


@mcp.tool(
    name="masters_counters_get",
    description="Read Campaign Wizard counters. See tool_help('masters_counters_get').",
)
@handle_cli_errors
def masters_counters_get(campaign_id: str) -> dict:
    """Get the campaign's linked Yandex Metrika counters.

    Requires a direct-cli release containing commit
    https://github.com/axisrow/direct-cli/commit/a52fe95. The command is absent
    from the published 0.5.2 wheel.

    Args:
        campaign_id: Campaign ID.
    """
    return _get_campaign_resource("masters_counters_get", campaign_id)


@mcp.tool(
    name="masters_audience_get",
    description="Read Campaign Wizard audience. See tool_help('masters_audience_get').",
)
@handle_cli_errors
def masters_audience_get(campaign_id: str) -> dict:
    """Get the campaign's manual audience settings.

    Args:
        campaign_id: Campaign ID.
    """
    return _get_campaign_resource("masters_audience_get", campaign_id)


@mcp.tool(
    name="masters_add",
    description=(
        "Create a Wizard campaign — MUTATING, NOT idempotent; no rollback. "
        "Draft by default; draft=False launches. See tool_help('masters_add')."
    ),
)
@handle_cli_errors
def masters_add(
    url: str,
    headlines: list[str],
    texts: list[str],
    add_target_actions: list[str],
    weekly_budget: int,
    region_options: dict | None = None,
    draft: bool = True,
) -> dict:
    """Create a new Мастер кампаний ("Конверсии и трафик") campaign.

    MUTATING and NOT idempotent: running this twice with the same arguments
    creates a SECOND campaign — Мастер кампаний has no duplicate detection and
    no sandbox/rollback. Double-check the arguments before calling.

    The campaign is saved as a DRAFT by default (``draft=True``). Pass
    ``draft=False`` to launch it immediately — unlike the raw CLI (whose own
    default launches), the plugin defaults to the safe draft path.

    Args:
        url: Landing page URL the wizard optimizes for.
        headlines: Ad headline variants (Варианты заголовков); repeat for
            multiple. The wizard refuses to auto-generate copy, so explicit
            text is required.
        texts: Ad text variants (Варианты текстов объявлений).
        add_target_actions: Conversion goals as ``"goal_id=price"`` (Yandex
            Metrika goal ID = CPA in account currency); repeat for multiple
            goals. At least one is required — the create form silently refuses
            without a goal. The goal must belong to the Metrika counter on the
            landing page's domain.
        weekly_budget: Weekly budget in ACCOUNT CURRENCY (Недельный бюджет) —
            a plain number like 15000, NOT micro-units. Required; the create
            form silently refuses without one.
        region_options: Display region dict — keys: ``regions`` (list of exact
            Yandex region names), ``region_ids`` (list of RegionId strings,
            resolved via the GeoRegions dictionary; needs API credentials,
            unlike the rest of this tool). At least one region overall is
            required; the two keys combine.
        draft: True (default) saves as a draft; False launches immediately.
    """
    values = locals()
    expansion_error = expand_grouped_dicts(values, MASTERS_ADD_DICT_REGISTRY)
    if expansion_error is not None:
        return tool_error_dict(expansion_error)

    args = [*_command_path("masters_add"), str(url)]
    append_cli_options(args, values, MASTERS_ADD_OPTIONS)
    return cast(dict, _run_browser_json(args, allow_nonzero=True))


def _append_directs_helps(args: list[str], values: dict) -> None:
    """Emit the tri-state --directs-helps/--no-directs-helps pair.

    The shared CliOption table cannot express the negative flag: is_flag=True
    only emits bare flags for truthy values, which would turn an explicit
    ``False`` into a silent no-op. ``None`` (not requested) emits nothing.
    """
    directs_helps = values.get("directs_helps")
    if directs_helps is True:
        args.append("--directs-helps")
    elif directs_helps is False:
        args.append("--no-directs-helps")


@mcp.tool(
    name="masters_update",
    description=(
        "Update Wizard campaigns — MUTATING; launch publishes a draft. "
        "See tool_help('masters_update')."
    ),
)
@handle_cli_errors
def masters_update(
    campaign_id: str | None = None,
    from_file: str | None = None,
    masters_json: list | str | None = None,
    dry_run: bool = False,
    launch: bool = False,
    budget_options: dict | None = None,
    goal_options: dict | None = None,
    creative_options: dict | None = None,
    media_options: dict | None = None,
    audience_options: dict | None = None,
    metrika_options: dict | None = None,
    batch_options: dict | None = None,
) -> list[dict] | dict:
    """Update settings of one or many Мастер кампаний campaigns.

    MUTATING: the edit page has a single whole-form save, so every passed
    field is committed to the LIVE campaign state in one save (fields not
    passed keep their current value). Lifecycle dependence: for a DRAFT
    campaign the default save keeps it a DRAFT; ``launch=True`` publishes it
    while saving (no effect on a non-DRAFT campaign; to publish without
    changing fields use ``masters_launch``). For a LIVE campaign the save
    applies immediately. ``launch`` stays a flat param on purpose — publishing
    a draft must not hide inside a dict.

    Modes (exactly one): single ``campaign_id`` + at least one field, or a
    batch plan via ``from_file`` (JSONL, one campaign object per line) or
    ``masters_json`` (inline JSON array) — mutually exclusive, and both are
    exclusive with ``campaign_id``. Batch rows are the source of truth:
    PascalCase keys mirroring the field names below (``CampaignId`` integer
    required per row, ``Headlines`` as a ``{"2": "text"}`` slot object, batch
    ``RemoveAudienceTags``/``RemoveMetrikaCounters``/``RemoveSitelinks`` are
    1-based while the flat params are 0-based — a direct-cli asymmetry).
    ``batch_options`` (``moderation_statuses`` snapshot flag, ``pacing_ms``)
    only applies to batch mode; the CLI rejects them in single mode.
    ``dry_run`` validates the plan (including that local image/video files
    exist) and prints it without opening a browser.

    Field dicts (keys = the flat param names; unknown keys are ignored
    silently, so spell them exactly):

    - ``budget_options``: weekly_budget (account currency, not micro-units),
      promotion_goal (max-clicks | max-conversions), goal_price,
      directs_helps (True → --directs-helps, False → --no-directs-helps).
    - ``goal_options``: target_action_prices, add_target_actions,
      remove_target_actions — "goal_id=price" strings / goal-id strings for
      the "Целевые действия" table (max-conversions gating; a goal id cannot
      appear in more than one of the three).
    - ``creative_options``: name, landing_url, tracking_params (pass "" to
      clear landing_url/tracking_params), headlines, texts (slot replacement
      ``"N=text"``, N 1-based: headlines 1-5, texts 1-3 — replaces an EXISTING
      variant, never adds), clear_headlines, clear_texts (1-based slot numbers
      to delete; a slot cannot be set and cleared in one call).
    - ``media_options``: images ("N=path", 1-based position; Yandex has no
      in-place image replacement — the new image is appended, so the set
      order changes), add_video, add_video_url, remove_videos (exact URLs;
      max 2 videos per campaign).
    - ``audience_options``: gender (any | female | male), age_from (0 | 18 |
      25 | 35 | 45 | 55), age_to (18 | 25 | 35 | 45 | 55 | unlimited),
      devices (list of mobile | desktop | tablet — REPLACES the whole
      selection), add_audience_tags (exact autocomplete suggestions),
      remove_audience_tags (0-based positions; see masters_audience_get).
    - ``metrika_options``: add_metrika_counters, remove_metrika_counters
      (0-based positions) AND the sitelinks pair add_sitelinks
      ("Title|Href|Description"), remove_sitelinks (0-based positions) — the
      sitelinks live under the same dict even though they are a separate UI
      section.
    - ``batch_options``: moderation_statuses (bool snapshot after each batch
      save — not a final moderation verdict), pacing_ms (pause between batch
      campaigns), no_progress (suppress the per-campaign stderr progress
      line).

    NOT LIVE-VERIFIED paths (the plugin cannot claim more certainty than the
    CLI): ``add_video``'s actual file-upload sequence (upload → poll → Save)
    was never confirmed against the real Yandex UI — prefer ``add_video_url``
    (fully live-verified); ``remove_metrika_counters`` (the add/link path is
    LIVE-VERIFIED through the page per direct-cli #846, the remove path is
    not); part of ``add_sitelinks`` (whether Yandex's inline form really
    requires a non-empty description is unconfirmed). There are no live tests
    for ``add_video`` — manual verification only.

    Args:
        campaign_id: Campaign ID for single mode.
        from_file: JSONL plan file path (batch mode).
        masters_json: Inline JSON array plan (batch mode); a JSON string or an
            already-parsed list/dict.
        dry_run: Validate and print the plan without opening a browser.
        launch: Publish a DRAFT campaign while saving (single mode).
        budget_options: Budget/goal-strategy dict — see above.
        goal_options: Target-action table dict — see above.
        creative_options: Name/URL/UTM/slot-copy dict — see above.
        media_options: Images/videos dict — see above.
        audience_options: Manual audience dict — see above.
        metrika_options: Counters + sitelinks dict — see above.
        batch_options: Batch-mode controls (moderation_statuses, pacing_ms,
            no_progress) — see above.
    """
    values = locals()
    expansion_error = expand_grouped_dicts(values, MASTERS_UPDATE_DICT_REGISTRY)
    if expansion_error is not None:
        return tool_error_dict(expansion_error)

    if from_file is not None or masters_json is not None:
        return _run_masters_update_batch(
            values,
            campaign_id=campaign_id,
            from_file=from_file,
            masters_json=masters_json,
            dry_run=dry_run,
        )

    if campaign_id is None:
        return tool_error_dict(
            ToolError(
                error="missing_mode",
                message=(
                    "Provide exactly one of: campaign_id (single campaign), "
                    "from_file (JSONL plan), or masters_json (inline JSON array)."
                ),
            )
        )

    fields_error = require_update_fields(
        values,
        message=(
            "Provide at least one field to update, via the grouped dicts: "
            "budget_options, goal_options, creative_options, media_options, "
            "audience_options, metrika_options (batch mode also takes "
            "batch_options)."
        ),
        exclude={"campaign_id", "from_file", "masters_json", "dry_run", "launch"},
    )
    if fields_error:
        return tool_error_dict(fields_error)

    # JSON hosts may send numeric age brackets (18, not "18"); the CLI Choice
    # accepts either spelling, so validate the string form.
    for field_name, allowed in _UPDATE_ENUM_GUARDS:
        if values.get(field_name) is None:
            continue
        enum_error = validate_enum(
            str(values[field_name]),
            allowed,
            field=field_name,
            error=f"invalid_{field_name}",
        )
        if enum_error:
            return tool_error_dict(enum_error)
    for device in values.get("devices") or ():
        enum_error = validate_enum(
            str(device), _DEVICE_CHOICES, field="devices", error="invalid_devices"
        )
        if enum_error:
            return tool_error_dict(enum_error)

    args = [*_command_path("masters_update"), str(campaign_id)]
    append_cli_options(args, values, MASTERS_UPDATE_OPTIONS)
    _append_directs_helps(args, values)
    if dry_run:
        args.append("--dry-run")
    return _run_browser_json(args, allow_nonzero=True)


def _run_masters_update_batch(
    values: dict,
    *,
    campaign_id: str | None,
    from_file: str | None,
    masters_json: list | str | None,
    dry_run: bool,
) -> list[dict] | dict:
    """Run the batch path of ``masters_update`` (from_file / masters_json)."""
    if campaign_id is not None:
        return tool_error_dict(
            ToolError(
                error="conflicting_modes",
                message=(
                    "campaign_id is for single-campaign mode; in batch mode "
                    "every plan row carries its own CampaignId. Pass "
                    "campaign_id OR from_file/masters_json, not both."
                ),
            )
        )
    if from_file is not None and masters_json is not None:
        return tool_error_dict(
            ToolError(
                error="conflicting_modes",
                message=(
                    "from_file and masters_json are mutually exclusive — "
                    "pass exactly one."
                ),
            )
        )

    # A pre-parsing MCP host may have decoded the plan into a list/dict; object
    # IDs inside it must survive the JavaScript round-trip (same guard as
    # helpers.run_batch_mutation).
    plan_json: str | None = masters_json if isinstance(masters_json, str) else None
    if masters_json is not None and not isinstance(masters_json, str):
        unsafe_path = _find_unsafe_json_integer(masters_json)
        if unsafe_path is not None:
            return tool_error_dict(
                ToolError(
                    error="unsafe_json_integer",
                    message=(
                        "masters_json contains an integer outside JavaScript's "
                        f"exact range at {unsafe_path}. An MCP host may already "
                        "have rounded it; encode object IDs as JSON strings or "
                        "pass the plan as a raw JSON string."
                    ),
                )
            )
        plan_json = normalize_json_arg(masters_json)

    args = [*_command_path("masters_update")]
    if from_file is not None:
        args.extend(["--from-file", from_file])
    elif plan_json is not None:
        args.extend(["--masters-json", plan_json])
    append_cli_options(args, values, MASTERS_UPDATE_OPTIONS)
    # Emit the tri-state flag here too rather than dropping it silently:
    # directs_helps is a single-item field, so the CLI rejects the batch call
    # with "put the field in the --from-file/--masters-json plan instead".
    _append_directs_helps(args, values)
    if dry_run:
        args.append("--dry-run")
    return cast(list[dict] | dict, _run_browser_json(args, allow_nonzero=True))
