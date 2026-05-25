"""MCP tools for bid modifier management."""

from server.main import mcp
from server.tools import ToolError, get_runner, handle_cli_errors
from server.tools.helpers import check_batch_limit


_BIDMOD_LEVELS = ("CAMPAIGN", "AD_GROUP")
_BIDMOD_TYPES = (
    "AD_GROUP_ADJUSTMENT",
    "DEMOGRAPHICS_ADJUSTMENT",
    "DESKTOP_ADJUSTMENT",
    "DESKTOP_ONLY_ADJUSTMENT",
    "INCOME_GRADE_ADJUSTMENT",
    "MOBILE_ADJUSTMENT",
    "REGIONAL_ADJUSTMENT",
    "RETARGETING_ADJUSTMENT",
    "SERP_LAYOUT_ADJUSTMENT",
    "SMART_AD_ADJUSTMENT",
    "SMART_TV_ADJUSTMENT",
    "TABLET_ADJUSTMENT",
    "VIDEO_ADJUSTMENT",
)


@mcp.tool(name="bidmodifiers_get")
@handle_cli_errors
def bidmodifiers_list(
    ids: str | None = None,
    campaign_ids: str | None = None,
    ad_group_ids: str | None = None,
    types: str | None = None,
    levels: str | None = None,
    limit: int | None = None,
    fetch_all: bool = False,
    fields: str | None = None,
) -> list[dict] | dict:
    """List bid modifiers.

    Args:
        ids: Comma-separated bid modifier IDs.
        campaign_ids: Comma-separated campaign IDs (max 10).
        ad_group_ids: Comma-separated ad group IDs (max 10).
        types: Comma-separated bid modifier types.
        levels: Level filter — "CAMPAIGN" or "AD_GROUP" (CLI default: both).
        limit: Limit number of results.
        fetch_all: Fetch all pages.
        fields: Comma-separated field names.
    """
    if levels is not None and levels not in _BIDMOD_LEVELS:
        return ToolError(
            error="invalid_levels",
            message=f"levels must be one of {_BIDMOD_LEVELS}; got '{levels}'",
        ).__dict__

    args = ["bidmodifiers", "get", "--format", "json"]
    if ids is not None:
        normalized = ids.strip()
        if normalized:
            args.extend(["--ids", normalized])
    normalized_campaign_ids = campaign_ids.strip() if campaign_ids is not None else None
    if normalized_campaign_ids:
        batch_error = check_batch_limit(normalized_campaign_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--campaign-ids", normalized_campaign_ids])
    normalized_ad_group_ids = ad_group_ids.strip() if ad_group_ids is not None else None
    if normalized_ad_group_ids:
        batch_error = check_batch_limit(normalized_ad_group_ids)
        if batch_error:
            return batch_error.__dict__
        args.extend(["--adgroup-ids", normalized_ad_group_ids])
    if types is not None:
        args.extend(["--types", types])
    if levels is not None:
        args.extend(["--levels", levels])
    if limit is not None:
        args.extend(["--limit", str(limit)])
    if fetch_all:
        args.append("--fetch-all")
    if fields is not None:
        args.extend(["--fields", fields])

    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="bidmodifiers_set")
@handle_cli_errors
def bidmodifiers_set(
    id: int,
    value: int,
    dry_run: bool = False,
) -> dict:
    """Update an existing bid modifier by ID.

    CLI 0.3.8 dropped --json. The only typed knob is --value.

    Args:
        id: Existing BidModifier ID returned by `bidmodifiers_add`.
        value: Modifier percentage integer (0–1300, e.g. 150 for +50%).
            Not money/micro-units.
        dry_run: Show the direct request without sending it.
    """
    args = [
        "bidmodifiers",
        "set",
        "--id",
        str(id),
        "--value",
        str(value),
    ]
    if dry_run:
        args.append("--dry-run")
    runner = get_runner()
    return runner.run_json(args)


@mcp.tool(name="bidmodifiers_delete")
@handle_cli_errors
def bidmodifiers_delete(ids: str, dry_run: bool = False) -> dict:
    """Delete bid modifiers.

    Args:
        ids: Comma-separated modifier IDs (max 10).
    """
    from server.tools.helpers import run_single_id_batch

    return run_single_id_batch(
        get_runner(), "bidmodifiers", "delete", ids, dry_run=dry_run
    )


@mcp.tool(name="bidmodifiers_add")
@handle_cli_errors
def bidmodifiers_add(
    modifier_type: str,
    value: int,
    campaign_id: int | None = None,
    ad_group_id: int | None = None,
    gender: str | None = None,
    age: str | None = None,
    retargeting_condition_id: int | None = None,
    region_id: int | None = None,
    serp_layout: str | None = None,
    income_grade: str | None = None,
    operating_system_type: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Add a bid modifier.

    Args:
        modifier_type: Bid modifier type (MOBILE_ADJUSTMENT, DEMOGRAPHICS_ADJUSTMENT, …).
        value: Bid modifier percentage (0–1300).
        campaign_id: Campaign ID (mutually exclusive with ad_group_id).
        ad_group_id: Ad group ID (mutually exclusive with campaign_id).
        gender: Demographics adjustment gender.
        age: Demographics adjustment age value.
        retargeting_condition_id: Retargeting condition ID.
        region_id: Regional adjustment region ID.
        serp_layout: SERP layout adjustment value.
        income_grade: Income grade adjustment value.
        dry_run: Show the direct request without sending it.
    """
    if modifier_type not in _BIDMOD_TYPES:
        return ToolError(
            error="invalid_modifier_type",
            message=(
                f"modifier_type must be one of {_BIDMOD_TYPES}; got '{modifier_type}'"
            ),
        ).__dict__
    if campaign_id is None and ad_group_id is None:
        return ToolError(
            error="missing_target_scope",
            message="Provide at least one of: campaign_id, ad_group_id",
        ).__dict__

    args = ["bidmodifiers", "add", "--type", modifier_type, "--value", str(value)]
    if campaign_id is not None:
        args.extend(["--campaign-id", str(campaign_id)])
    if ad_group_id is not None:
        args.extend(["--adgroup-id", str(ad_group_id)])
    if gender is not None:
        args.extend(["--gender", gender])
    if age is not None:
        args.extend(["--age", age])
    if retargeting_condition_id is not None:
        args.extend(["--retargeting-condition-id", str(retargeting_condition_id)])
    if region_id is not None:
        args.extend(["--region-id", str(region_id)])
    if serp_layout is not None:
        args.extend(["--serp-layout", serp_layout])
    if income_grade is not None:
        args.extend(["--income-grade", income_grade])
    if operating_system_type is not None:
        args.extend(["--operating-system-type", operating_system_type])
    if dry_run:
        args.append("--dry-run")

    runner = get_runner()
    return runner.run_json(args)
