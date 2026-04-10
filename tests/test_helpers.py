"""Tests for shared tool helpers."""

from server.tools import ToolError
from server.tools.helpers import (
    check_batch_limit,
    parse_ids,
    run_single_id_batch,
    validate_positive_int,
    validate_state,
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


# --- validate_state ---


def test_validate_state_valid():
    assert validate_state("ON", ("ON", "OFF")) is None


def test_validate_state_invalid():
    result = validate_state("MAYBE", ("ON", "OFF"))
    assert isinstance(result, ToolError)
    assert result.error == "invalid_state"


# --- validate_positive_int ---


def test_validate_positive_int_valid():
    assert validate_positive_int("42", "bid") == 42


def test_validate_positive_int_zero():
    result = validate_positive_int("0", "bid")
    assert isinstance(result, ToolError)
    assert result.error == "invalid_value"


def test_validate_positive_int_negative():
    result = validate_positive_int("-5", "bid")
    assert isinstance(result, ToolError)


def test_validate_positive_int_non_numeric():
    result = validate_positive_int("abc", "bid")
    assert isinstance(result, ToolError)


def test_validate_positive_int_float_string():
    result = validate_positive_int("3.14", "bid")
    assert isinstance(result, ToolError)
