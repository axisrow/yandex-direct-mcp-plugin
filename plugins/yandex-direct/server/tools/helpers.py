"""Shared helpers for MCP tool modules."""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from server.cli.runner import (
    CliAuthError,
    CliError,
    CliNotFoundError,
    CliRegistrationError,
    CliTimeoutError,
)
from server.tools import ToolError, _hint_for_cli_error, tool_error_dict

MAX_BATCH_SIZE = 10


@dataclass(frozen=True)
class CliOption:
    """Declarative mapping from an MCP parameter to a `direct` CLI flag."""

    name: str
    flag: str
    repeat: bool = False
    is_flag: bool = False


def append_cli_options(
    args: list[str],
    values: Mapping[str, object],
    options: Sequence[CliOption],
) -> None:
    """Append optional `direct` CLI flags from function locals."""
    for option in options:
        value = values.get(option.name)
        if value is None:
            continue
        if option.is_flag:
            if value:
                args.append(option.flag)
            continue
        if option.repeat:
            if not value:
                continue
            if isinstance(value, str):
                args.extend([option.flag, value])
                continue
            if not isinstance(value, Iterable):
                args.extend([option.flag, str(value)])
                continue
            for item in value:
                args.extend([option.flag, str(item)])
            continue
        args.extend([option.flag, str(value)])


def expand_grouped_dicts(
    values: dict,
    registry: Sequence[tuple[str, Sequence[str]]],
) -> ToolError | None:
    """Expand grouped dict params into flat option keys in *values*.

    Wide mutate tools expose families of flat params as a single nested
    ``dict | None`` param to shrink the JSON Schema FastMCP broadcasts at startup
    (#220). At call time the incoming dict is expanded back into the individual
    option names that :func:`append_cli_options` expects, so the generated CLI
    argv is byte-for-byte identical to the old flat signature.

    *registry* maps each dict param name to the flat option names it absorbs.
    Mutates *values* in place. Returns a :class:`ToolError` on a non-dict value
    (e.g. a string), else ``None``. Unknown keys inside a group dict are silently
    ignored — forward-compatible with new CLI flags. **Caveat for callers:**
    a typo in a key (e.g. ``pirce_extension_price``) is therefore a silent no-op;
    dict-key spelling must match the registry exactly.
    """
    for dict_name, member_names in registry:
        incoming = values.get(dict_name)
        if incoming is None:
            continue
        if not isinstance(incoming, dict):
            return ToolError(
                error="invalid_param",
                message=(
                    f"'{dict_name}' must be a dict or null, "
                    f"got {type(incoming).__name__}"
                ),
            )
        for member in member_names:
            if member in incoming:
                values[member] = incoming[member]
    return None


def parse_ids(ids_str: str) -> list[str]:
    """Parse comma-separated IDs string into a list."""
    return [id.strip() for id in ids_str.split(",") if id.strip()]


def check_batch_limit(ids_str: str, max_size: int = MAX_BATCH_SIZE) -> ToolError | None:
    """Validate batch size of comma-separated IDs."""
    ids = parse_ids(ids_str)
    if len(ids) > max_size:
        return ToolError(
            error="batch_limit",
            message=f"Maximum {max_size} IDs per request. Got: {len(ids)}",
        )
    return None


def provided_update_value(value: object) -> bool:
    """Return whether an optional update value should satisfy update guards."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def normalize_optional_str(value: str | None) -> str | None:
    """Strip an optional string and collapse blanks to None."""
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def normalize_str_list(values: list[str] | None) -> list[str]:
    """Strip list items and drop blanks."""
    if not values:
        return []
    return [value.strip() for value in values if value.strip()]


def finalize_json_args(args: list[str], dry_run: bool) -> list[str]:
    """Append optional dry-run and JSON output flags."""
    if dry_run:
        args.append("--dry-run")
    args.extend(["--format", "json"])
    return args


def run_batch_mutation(
    runner,
    resource: str,
    action: str,
    *,
    from_file: str | None,
    json_arg: str | None,
    json_flag: str,
    default_id_flag: str | None = None,
    default_id: int | None = None,
    dry_run: bool = False,
) -> dict | None:
    """Dispatch the batch path of an add/update tool.

    A batch is requested when either ``from_file`` (a JSONL path) or
    ``json_arg`` (an inline JSON array) is given. Returns:

    - ``None`` — no batch input; the caller runs its single-item path.
    - an error dict — both batch inputs given (mutually exclusive).
    - the CLI result dict — the CLI was invoked for the batch.

    ``default_id``/``default_id_flag`` forward an optional batch-default scope
    (e.g. ``--adgroup-id`` for ads, ``--campaign-id`` for ad groups) that rows
    may override. Single-item content fields the caller may also have received
    are NOT forwarded here — in batch mode the file/JSON rows are the source of
    truth, so any stray single-item field is ignored (callers should document
    this).
    """
    if not from_file and not json_arg:
        return None
    if from_file and json_arg:
        return tool_error_dict(
            ToolError(
                error="conflicting_modes",
                message=(
                    f"from_file and {json_flag.lstrip('-').replace('-', '_')} are "
                    "mutually exclusive — pass exactly one."
                ),
            )
        )

    args = [resource, action]
    if default_id is not None and default_id_flag is not None:
        args.extend([default_id_flag, str(default_id)])
    if from_file:
        args.extend(["--from-file", from_file])
    if json_arg:
        args.extend([json_flag, json_arg])
    if dry_run:
        args.append("--dry-run")
    return runner.run_json(args)


def validate_phrase_csv(
    phrases: str,
    max_count: int,
    *,
    subject: str,
) -> str | ToolError:
    """Validate a comma-separated phrase list against a max-count limit.

    Strips the input, counts non-empty CSV items, and returns the normalized
    string when valid. Returns a ToolError with the same payload v4forecast /
    v4wordstat produced inline before: error="missing_phrases" when empty,
    error="phrases_limit" (message "Maximum {max_count} phrases per {subject}.
    Got: {n}") when over the limit.
    """
    normalized = phrases.strip()
    phrase_count = (
        sum(1 for phrase in normalized.split(",") if phrase.strip())
        if normalized
        else 0
    )
    if phrase_count == 0:
        return ToolError(
            error="missing_phrases",
            message="Provide at least one phrase.",
        )
    if phrase_count > max_count:
        return ToolError(
            error="phrases_limit",
            message=f"Maximum {max_count} phrases per {subject}. Got: {phrase_count}",
        )
    return normalized


def validate_state(state: str, allowed: tuple[str, ...]) -> ToolError | None:
    """Validate state value against allowed options."""
    if state not in allowed:
        return ToolError(
            error="invalid_state",
            message=f"State must be one of {allowed}. Got: '{state}'",
        )
    return None


def validate_yes_no(value: str, *, field: str, error: str) -> ToolError | None:
    """Validate a YES/NO flag, returning a ToolError | None.

    Several tools repeat the same inline check for "YES"/"NO" CLI flags. The
    ``field``/``error`` parameters preserve each call site's existing payload
    (error key + message), so the wire contract is unchanged.
    """
    if value not in ("YES", "NO"):
        return ToolError(
            error=error,
            message=f"{field} must be YES or NO; got '{value}'",
        )
    return None


def validate_positive_int(value: str, field_name: str) -> int | ToolError:
    """Validate and convert string to positive integer. Returns int or ToolError."""
    try:
        result = int(value)
        if result <= 0:
            raise ValueError(f"{field_name} must be positive")
        return result
    except (ValueError, TypeError):
        return ToolError(
            error="invalid_value",
            message=f"{field_name} must be a positive integer. Got: '{value}'",
        )


def run_single_id_batch(
    runner,
    resource: str,
    action: str,
    ids_str: str,
    dry_run: bool = False,
) -> dict:
    """Run a single-ID CLI mutation for a comma-separated batch of IDs.

    Each individual CLI invocation gets the optional --dry-run flag when
    `dry_run=True`. Use this for any *_delete / *_archive / *_unarchive /
    *_suspend / *_resume / *_moderate batch wrapper.
    """
    batch_error = check_batch_limit(ids_str)
    if batch_error:
        return tool_error_dict(batch_error)

    ids = parse_ids(ids_str)
    if not ids:
        return tool_error_dict(
            ToolError(
                error="missing_ids",
                message=f"Provide at least one {resource} ID.",
            )
        )
    results = []
    succeeded = []
    failed = []
    for item_id in ids:
        argv = [resource, action, "--id", item_id]
        if dry_run:
            argv.append("--dry-run")
        try:
            result = runner.run_json(argv)
            results.append(result)
            succeeded.append(item_id)
        except (CliAuthError, CliNotFoundError, CliRegistrationError, CliTimeoutError):
            raise
        except Exception as e:
            item_error: dict = {"success": False, "id": item_id, "error": str(e)}
            if isinstance(e, CliError):
                hint = _hint_for_cli_error(e)
                if hint is not None:
                    item_error["hint"] = hint
            results.append(item_error)
            failed.append(item_id)
    if len(results) == 1:
        return results[0]
    return {
        "success": len(failed) == 0,
        "ids": ids,
        "succeeded": succeeded,
        "failed": failed,
        "results": results,
    }


def run_set_bids(
    runner,
    resource: str,
    *,
    id: int | None = None,
    ad_group_id: int | None = None,
    campaign_id: int | None = None,
    bid_fields: Sequence[tuple[str, object | None]],
    missing_update_message: str,
    dry_run: bool = False,
) -> dict:
    """Run a target set-bids command with shared scope/update guards."""
    if id is None and ad_group_id is None and campaign_id is None:
        return tool_error_dict(
            ToolError(
                error="missing_target_scope",
                message="Provide at least one of: id, ad_group_id, campaign_id",
            )
        )
    if not any(value is not None for _, value in bid_fields):
        return tool_error_dict(
            ToolError(
                error="missing_update_fields",
                message=missing_update_message,
            )
        )

    args = [resource, "set-bids"]
    if id is not None:
        args.extend(["--id", str(id)])
    if ad_group_id is not None:
        args.extend(["--adgroup-id", str(ad_group_id)])
    if campaign_id is not None:
        args.extend(["--campaign-id", str(campaign_id)])
    for flag, value in bid_fields:
        if value is not None:
            args.extend([flag, str(value)])
    if dry_run:
        args.append("--dry-run")
    return runner.run_json(args)
