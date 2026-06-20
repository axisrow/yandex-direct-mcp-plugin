"""Tests for shared tool helpers."""

from server.tools import ToolError
from server.tools.helpers import (
    append_id_filters,
    append_pagination,
    check_batch_limit,
    parse_ids,
    require_non_empty_list,
    require_update_fields,
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


# --- require_update_fields ---


def test_require_update_fields_none_provided_returns_error():
    values = {"id": 5, "dry_run": False, "name": None, "budget": None}
    result = require_update_fields(
        values, message="Provide at least one field.", exclude={"id", "dry_run"}
    )
    assert isinstance(result, ToolError)
    assert result.error == "missing_update_fields"
    assert result.message == "Provide at least one field."


def test_require_update_fields_one_provided_returns_none():
    values = {"id": 5, "dry_run": False, "name": "x", "budget": None}
    assert require_update_fields(values, message="m", exclude={"id", "dry_run"}) is None


def test_require_update_fields_excluded_value_does_not_count():
    # Only the excluded `type` is set — that must NOT satisfy the guard.
    values = {"id": 5, "type": "TEXT_AD", "title": None}
    result = require_update_fields(
        values, message="m", exclude={"id", "dry_run", "type"}
    )
    assert isinstance(result, ToolError)


def test_require_update_fields_uses_provided_update_value_semantics():
    # False / empty collections do not count as provided.
    values = {"id": 5, "flag": False, "items": [], "blob": {}}
    result = require_update_fields(values, message="m", exclude={"id"})
    assert isinstance(result, ToolError)


def test_require_update_fields_empty_string_and_zero_count_as_provided():
    # The standardization for the former raw-truthiness sites (ads/agency/
    # negative_keyword_shared_sets/retargeting): an empty string or integer 0 is
    # a *provided* field (provided_update_value semantics), unlike raw any().
    assert (
        require_update_fields({"id": 1, "name": ""}, message="m", exclude={"id"})
        is None
    )
    assert (
        require_update_fields({"id": 1, "bid": 0}, message="m", exclude={"id"}) is None
    )


# --- append_pagination ---


def test_append_pagination_all_set():
    args = ["x", "get"]
    append_pagination(args, 50, True, "Id,Name")
    assert args == ["x", "get", "--limit", "50", "--fetch-all", "--fields", "Id,Name"]


def test_append_pagination_omits_unset():
    args = ["x", "get"]
    append_pagination(args, None, False, None)
    assert args == ["x", "get"]


def test_append_pagination_order_limit_then_fetchall_then_fields():
    args = []
    append_pagination(args, 1, True, "Id")
    assert args == ["--limit", "1", "--fetch-all", "--fields", "Id"]


def test_append_pagination_zero_limit_is_emitted():
    # limit=0 is a valid limit (is-not-None guard), not silently dropped.
    args = ["x", "get"]
    append_pagination(args, 0, False, None)
    assert args == ["x", "get", "--limit", "0"]


# --- append_id_filters ---


def test_append_id_filters_emits_in_order_and_strips():
    args = ["x", "get"]
    append_id_filters(
        args,
        [(" 1,2 ", "--campaign-ids"), ("3", "--ids"), (None, "--adgroup-ids")],
    )
    assert args == ["x", "get", "--campaign-ids", "1,2", "--ids", "3"]


def test_append_id_filters_drops_empty_and_whitespace():
    # Empty / whitespace-only values are dropped, never forwarded as `--flag ''`.
    args = ["x", "get"]
    append_id_filters(args, [("", "--campaign-ids"), ("   ", "--ids")])
    assert args == ["x", "get"]
