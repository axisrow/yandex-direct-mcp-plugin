"""Regression tests for issue #258.

PR #257 (#256) migrated int64 object-ID params from ``int`` to ``str`` across
the v5 tool surface — a JS MCP host rounds big int64 IDs through float64
before Python ever sees them, since FastMCP publishes a bare ``int`` param as
``{"type": "integer"}`` in the JSON Schema. The v4-Live tools
(v4account/v4wordstat/v4forecast) were explicitly left out of that migration's
scope; this file closes the gap for them.
"""

import asyncio

import pytest

from server.main import mcp

# An int64 ID above 2**53 (9_007_199_254_740_992): its last three digits are
# exactly what a float64 round-trip destroys.
BIG_ID = 1915883588174806058
BIG_ID_STR = "1915883588174806058"


def _schema_types(param_schema: dict) -> set[str]:
    """Collect the JSON-Schema ``type`` tokens for a (possibly anyOf) param."""
    if "anyOf" in param_schema:
        types: set[str] = set()
        for branch in param_schema["anyOf"]:
            if "type" in branch:
                types.add(branch["type"])
        return types
    if "type" in param_schema:
        return {param_schema["type"]}
    return set()


def _tool_schema(name: str) -> dict:
    tools = asyncio.run(mcp.list_tools())
    return next(t.inputSchema for t in tools if t.name == name)


# --------------------------------------------------------------------------- #
# int64 object-ID params must NOT publish a bare integer type.                #
# --------------------------------------------------------------------------- #

ID_PARAMS = [
    ("v4account_update_account", "account_id"),
    ("v4account_transfer_money", "from_account_id"),
    ("v4account_transfer_money", "to_account_id"),
    ("v4wordstat_get_report", "report_id"),
    ("v4wordstat_delete_report", "report_id"),
    ("v4forecast_get", "forecast_id"),
    ("v4forecast_delete", "forecast_id"),
]


@pytest.mark.parametrize("tool_name,param", ID_PARAMS)
def test_v4_id_params_are_strings_not_integers(tool_name, param):
    """int64 IDs must be typed string in the schema so a JS host cannot round
    them through float64 before Python sees them (#258, mirrors #256)."""
    schema = _tool_schema(tool_name)
    props = schema.get("properties", {})
    assert param in props, f"{tool_name} lost param {param}"
    types = _schema_types(props[param])
    assert "string" in types, f"{tool_name}.{param} should accept string, got {types}"
    assert "integer" not in types, (
        f"{tool_name}.{param} still publishes an integer type — a big int64 ID "
        f"would be rounded by a JS MCP host before reaching Python. Types: {types}"
    )


# Non-object numeric params that must STAY integer — the migration must not
# over-reach into pagination, percentages, or caller-generated idempotency
# numbers, which are not int64 object IDs assigned by Yandex.
NON_ID_INT_PARAMS = [
    ("v4account_update_account", "money_warning_value"),
    ("v4account_deposit", "operation_num"),
    ("v4account_invoice", "operation_num"),
    ("v4account_transfer_money", "operation_num"),
    ("v4adimage_get", "limit"),
    ("v4adimage_get", "offset"),
    ("v4events_get_events_log", "limit"),
    ("v4events_get_events_log", "offset"),
]


@pytest.mark.parametrize("tool_name,param", NON_ID_INT_PARAMS)
def test_v4_non_object_id_params_stay_integer(tool_name, param):
    """Guard against over-migration: pagination/percentage/idempotency params
    are NOT int64 object IDs and must keep their integer schema type (#258)."""
    schema = _tool_schema(tool_name)
    props = schema.get("properties", {})
    assert param in props, f"{tool_name} lost param {param}"
    types = _schema_types(props[param])
    assert "integer" in types, (
        f"{tool_name}.{param} should stay an integer (not an object ID) — the "
        f"int→str migration must not touch it. Types: {types}"
    )


# --------------------------------------------------------------------------- #
# A big int64 ID flows through the tool body to CLI argv unchanged.           #
# --------------------------------------------------------------------------- #


def test_big_int64_account_id_reaches_argv_intact_as_string():
    from unittest.mock import patch

    from server.tools.v4account import v4account_update_account
    from tests.helpers import mock_runner

    runner = mock_runner({"success": True})
    with patch("server.tools.v4account.get_runner", return_value=runner):
        v4account_update_account(
            account_id=BIG_ID_STR, day_budget="1000", spend_mode="Default", dry_run=True
        )
    argv = runner.run_json.call_args[0][0]
    assert BIG_ID_STR in argv


def test_big_int64_report_id_survives_dispatch_layer():
    """Through the real FastMCP dispatch layer, a string big-int ID is forwarded
    verbatim — this is the layer that used to round bare integers (#258)."""
    from unittest.mock import patch

    from tests.helpers import mock_runner

    runner = mock_runner({"success": True})
    with patch("server.tools.v4wordstat.get_runner", return_value=runner):
        asyncio.run(
            mcp.call_tool(
                "v4wordstat_get_report",
                {"report_id": BIG_ID_STR},
            )
        )
    argv = runner.run_json.call_args[0][0]
    assert BIG_ID_STR in argv


def test_big_int64_forecast_id_survives_dispatch_layer():
    from unittest.mock import patch

    from tests.helpers import mock_runner

    runner = mock_runner({"success": True})
    with patch("server.tools.v4forecast.get_runner", return_value=runner):
        asyncio.run(
            mcp.call_tool(
                "v4forecast_delete",
                {"forecast_id": BIG_ID_STR, "dry_run": True},
            )
        )
    argv = runner.run_json.call_args[0][0]
    assert BIG_ID_STR in argv
