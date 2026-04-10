"""Shared helpers for MCP tool modules."""

from server.tools import ToolError

MAX_BATCH_SIZE = 10


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


def validate_state(state: str, allowed: tuple[str, ...]) -> ToolError | None:
    """Validate state value against allowed options."""
    if state not in allowed:
        return ToolError(
            error="invalid_state",
            message=f"State must be one of {allowed}. Got: '{state}'",
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


def run_single_id_batch(runner, resource: str, action: str, ids_str: str) -> dict:
    """Run a single-ID CLI mutation for a comma-separated batch of IDs."""
    batch_error = check_batch_limit(ids_str)
    if batch_error:
        return batch_error.__dict__

    ids = parse_ids(ids_str)
    results = [runner.run_json([resource, action, "--id", item_id]) for item_id in ids]
    if len(results) == 1:
        return results[0]
    success = all(
        not isinstance(result, dict) or result.get("success", True) is not False
        for result in results
    )
    return {"success": success, "ids": ids, "results": results}
