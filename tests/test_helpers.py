"""Tests for shared tool helpers."""

from server.tools import ToolError
from server.tools.helpers import (
    check_batch_limit,
    parse_ids,
    require_non_empty_list,
    run_single_id_batch,
    validate_enum,
)


# --- parse_ids ---


def test_parse_ids_normal():
    assert parse_ids("1,2,3") == ["1", "2", "3"]


def test_parse_ids_with_spaces():
    assert parse_ids(" 1 , 2 , 3 ") == ["1", "2", "3"]


def test_parse_ids_single():
    assert parse_ids("42") == ["42"]


def test_parse_ids_empty():
    assert parse_ids("") == []


def test_parse_ids_only_commas():
    assert parse_ids(",,,") == []


# --- check_batch_limit ---


def test_check_batch_limit_under():
    assert check_batch_limit("1,2,3") is None


def test_check_batch_limit_at_limit():
    ids = ",".join(str(i) for i in range(10))
    assert check_batch_limit(ids) is None


def test_check_batch_limit_over():
    ids = ",".join(str(i) for i in range(11))
    result = check_batch_limit(ids)
    assert isinstance(result, ToolError)
    assert result.error == "batch_limit"


def test_check_batch_limit_custom_size():
    result = check_batch_limit("1,2,3", max_size=2)
    assert isinstance(result, ToolError)


def test_check_batch_limit_empty():
    assert check_batch_limit("") is None


def test_run_single_id_batch_rejects_empty_ids():
    runner = object()
    result = run_single_id_batch(runner, "vcards", "delete", "")
    assert result["error"] == "missing_ids"


def test_run_single_id_batch_rejects_whitespace_ids():
    runner = object()
    result = run_single_id_batch(runner, "vcards", "delete", "   ")
    assert result["error"] == "missing_ids"


def test_run_single_id_batch_batches_multiple_ids():
    runner = type("Runner", (), {})()
    runner.run_json = lambda args: {"success": True, "args": args}

    result = run_single_id_batch(runner, "vcards", "delete", "1,2")

    assert result["success"] is True
    assert result["ids"] == ["1", "2"]
    assert result["results"] == [
        {"success": True, "args": ["vcards", "delete", "--id", "1"]},
        {"success": True, "args": ["vcards", "delete", "--id", "2"]},
    ]


# --- validate_enum ---


def test_validate_enum_valid():
    assert (
        validate_enum("ON", ("ON", "OFF"), field="state", error="invalid_state") is None
    )


def test_validate_enum_invalid_preserves_payload():
    result = validate_enum("MAYBE", ("ON", "OFF"), field="state", error="invalid_state")
    assert isinstance(result, ToolError)
    assert result.error == "invalid_state"
    # Message format is part of the wire contract folded onto this helper.
    assert result.message == "state must be one of ('ON', 'OFF'); got 'MAYBE'"


# --- require_non_empty_list ---


def test_require_non_empty_list_returns_normalized():
    assert require_non_empty_list([" a ", "", "b"], error="missing_ids", noun="ID") == [
        "a",
        "b",
    ]


def test_require_non_empty_list_empty_returns_error():
    result = require_non_empty_list([], error="missing_ids", noun="video ID")
    assert isinstance(result, ToolError)
    assert result.error == "missing_ids"
    assert result.message == "Provide at least one video ID."


def test_require_non_empty_list_blanks_only_returns_error():
    result = require_non_empty_list(
        ["  ", ""], error="missing_keywords", noun="keyword"
    )
    assert isinstance(result, ToolError)
    assert result.error == "missing_keywords"
