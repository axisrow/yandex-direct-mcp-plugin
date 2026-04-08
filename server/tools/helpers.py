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
