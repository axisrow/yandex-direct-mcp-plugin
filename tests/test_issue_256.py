"""Regression tests for issue #256.

Four independent bugs surfaced while uploading a batch of TEXT_AD ads:

1. int64 ad IDs (~1.9e18, above 2**53) lost precision because ID params were
   typed ``int`` → the published JSON Schema said ``{"type": "integer"}`` → a
   JS MCP host rounds the big int through float64 before Python ever sees it.
2. ``keywords_json`` / ``ads_json`` / ``adgroups_json`` were typed ``str``, but
   MCP hosts pre-parse a JSON array into a Python ``list`` → pydantic rejected
   it with ``string_type`` and batch add was impossible.
3. A successful run's residual stderr (a potential warning source) was dropped
   by ``run_json``; API Warnings + Details that DO travel in stdout must reach
   the caller intact.
4. ``adimages_add`` used the 30 s default timeout; large JPEGs time out.
"""

import asyncio
import json
from unittest.mock import patch

import pytest

from server.cli.runner import DirectCliRunner
from server.main import mcp
from server.tools import ToolError, tool_error_dict
from server.tools.helpers import normalize_json_arg
from server.tools.images import ADIMAGES_ADD_TIMEOUT_SECONDS, adimages_add
from server.tools.keywords import keywords_add
from tests.helpers import mock_runner

# An int64 ad ID above 2**53 (9_007_199_254_740_992): its last three digits are
# exactly what a float64 round-trip destroys.
BIG_AD_ID = 1915883588174806058
BIG_AD_ID_STR = "1915883588174806058"


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
# #1 — int64 ID precision: ID params must NOT publish a bare integer type.     #
# --------------------------------------------------------------------------- #

ID_PARAMS = [
    ("ads_update", "id"),
    ("ads_update", "vcard_id"),
    ("ads_update", "sitelink_set_id"),
    ("ads_update", "turbo_page_id"),
    ("ads_update", "business_id"),
    ("ads_add", "ad_group_id"),
    ("ads_add", "vcard_id"),
    ("ads_add", "sitelink_set_id"),
    ("ads_add", "turbo_page_id"),
    ("ads_add", "business_id"),
    ("ads_add", "creative_id"),
    ("ads_add", "feed_id"),
    ("adgroups_add", "campaign_id"),
    ("adgroups_add", "feed_id"),
    ("adgroups_update", "id"),
    ("adgroups_update", "feed_id"),
    ("keywords_add", "ad_group_id"),
    ("keywords_update", "id"),
]


@pytest.mark.parametrize("tool_name,param", ID_PARAMS)
def test_id_params_are_strings_not_integers(tool_name, param):
    """int64 IDs must be typed string in the schema so a JS host cannot round
    them through float64 before Python sees them (#256-1)."""
    schema = _tool_schema(tool_name)
    props = schema.get("properties", {})
    assert param in props, f"{tool_name} lost param {param}"
    types = _schema_types(props[param])
    assert "string" in types, f"{tool_name}.{param} should accept string, got {types}"
    assert "integer" not in types, (
        f"{tool_name}.{param} still publishes an integer type — a big int64 ID "
        f"would be rounded by a JS MCP host before reaching Python. Types: {types}"
    )


def test_big_int64_id_reaches_argv_without_rounding():
    """A precise int64 ad ID passed as a string reaches the CLI argv intact —
    the last three digits are not zeroed (#256-1)."""
    runner = mock_runner({"success": True})
    with patch("server.tools.ads.get_runner", return_value=runner):
        from server.tools.ads import ads_update

        ads_update(id=BIG_AD_ID_STR, type="TEXT_AD", title="new title")
    argv = runner.run_json.call_args[0][0]
    assert BIG_AD_ID_STR in argv
    # The rounded form a float64 round-trip would produce must NOT appear.
    assert "1915883588174806000" not in argv


def test_big_int64_id_survives_dispatch_layer():
    """Through the real FastMCP dispatch layer, a string big-int ID is forwarded
    verbatim — this is the layer that used to round integers (#256-1)."""
    runner = mock_runner({"success": True})
    with patch("server.tools.ads.get_runner", return_value=runner):
        asyncio.run(
            mcp.call_tool(
                "ads_update",
                {"id": BIG_AD_ID_STR, "type": "TEXT_AD", "title": "x"},
            )
        )
    argv = runner.run_json.call_args[0][0]
    assert BIG_AD_ID_STR in argv


# --------------------------------------------------------------------------- #
# #2 — *_json batch params accept a pre-parsed list, not only a string.        #
# --------------------------------------------------------------------------- #


def test_normalize_json_arg_forms():
    """normalize_json_arg accepts str, list, dict, and blanks uniformly."""
    assert normalize_json_arg(None) is None
    assert normalize_json_arg("") is None
    assert normalize_json_arg("   ") is None
    assert normalize_json_arg('[{"Keyword":"x"}]') == '[{"Keyword":"x"}]'
    # A list from a pre-parsing host is re-serialized to a JSON string.
    out = normalize_json_arg([{"Keyword": "x"}])
    assert json.loads(out) == [{"Keyword": "x"}]
    # Cyrillic keys stay readable (ensure_ascii=False).
    out_cyr = normalize_json_arg([{"Keyword": "сердце"}])
    assert "сердце" in out_cyr
    assert json.loads(out_cyr) == [{"Keyword": "сердце"}]


def test_json_batch_params_accept_array_type_in_schema():
    """The schema for *_json params must allow an array (list), not only a
    string, so a pre-parsing MCP host does not trip string_type (#256-2)."""
    for tool_name, param in (
        ("keywords_add", "keywords_json"),
        ("ads_add", "ads_json"),
        ("ads_update", "ads_json"),
        ("adgroups_add", "adgroups_json"),
        ("adgroups_update", "adgroups_json"),
    ):
        schema = _tool_schema(tool_name)
        types = _schema_types(schema["properties"][param])
        assert "array" in types, (
            f"{tool_name}.{param} must accept an array so a host that pre-parses "
            f"the JSON does not fail pydantic string_type. Types: {types}"
        )


def test_keywords_json_list_via_dispatch_reaches_cli():
    """The exact repro from the report: an already-parsed JSON array sent to
    keywords_json must succeed and reach --keywords-json as a JSON string,
    not raise a pydantic string_type validation error (#256-2)."""
    runner = mock_runner({"success": True})
    parsed = [{"Keyword": "---autotargeting"}, {"Keyword": "сердце"}]
    with patch("server.tools.keywords.get_runner", return_value=runner):
        asyncio.run(
            mcp.call_tool(
                "keywords_add",
                {"ad_group_id": "123", "keywords_json": parsed},
            )
        )
    argv = runner.run_json.call_args[0][0]
    assert "--keywords-json" in argv
    payload = argv[argv.index("--keywords-json") + 1]
    assert json.loads(payload) == parsed
    assert "--adgroup-id" in argv


def test_keywords_json_string_still_works():
    """The raw-string form of keywords_json is unchanged (#256-2)."""
    runner = mock_runner({"success": True})
    raw = '[{"Keyword":"x"}]'
    with patch("server.tools.keywords.get_runner", return_value=runner):
        keywords_add(ad_group_id="123", keywords_json=raw)
    argv = runner.run_json.call_args[0][0]
    assert "--keywords-json" in argv
    assert raw in argv


def test_ads_json_list_via_dispatch_reaches_cli():
    """ads_json also accepts a pre-parsed list (same root cause) (#256-2)."""
    runner = mock_runner({"success": True})
    parsed = [{"adgroup-id": "1", "title": "t"}]
    with patch("server.tools.ads.get_runner", return_value=runner):
        asyncio.run(mcp.call_tool("ads_add", {"ads_json": parsed}))
    argv = runner.run_json.call_args[0][0]
    assert "--ads-json" in argv
    assert json.loads(argv[argv.index("--ads-json") + 1]) == parsed


def test_keywords_add_conflicting_single_and_batch():
    """keyword + keywords_json is contradictory and rejected before dispatch."""
    runner = mock_runner({"success": True})
    with patch("server.tools.keywords.get_runner", return_value=runner):
        result = keywords_add(
            ad_group_id="1", keyword="foo", keywords_json=[{"Keyword": "x"}]
        )
    assert result["error"] == "conflicting_modes"
    runner.run_json.assert_not_called()


def test_keywords_add_missing_mode():
    """No keyword and no batch input yields the graceful missing_mode guard."""
    runner = mock_runner({"success": True})
    with patch("server.tools.keywords.get_runner", return_value=runner):
        result = keywords_add(ad_group_id="1")
    assert result["error"] == "missing_mode"
    runner.run_json.assert_not_called()


# --------------------------------------------------------------------------- #
# #3 — Warnings + Details are surfaced, not swallowed.                         #
# --------------------------------------------------------------------------- #


def _completed(stdout: str, stderr: str = "", returncode: int = 0):
    from subprocess import CompletedProcess

    return CompletedProcess(
        args=["direct"], returncode=returncode, stdout=stdout, stderr=stderr
    )


def test_stdout_warnings_with_details_pass_through():
    """API per-action Warnings (with Details) live in the stdout JSON and must
    reach the caller verbatim — the field that was hard to diagnose (#256-3)."""
    payload = [
        {
            "Id": BIG_AD_ID,
            "Warnings": [
                {
                    "Code": 10165,
                    "Message": "Parameter will not be applied",
                    "Details": "Title2 was merged into Title",
                }
            ],
        }
    ]
    runner = DirectCliRunner()
    with patch.object(runner, "run", return_value=_completed(json.dumps(payload))):
        result = runner.run_json(["ads", "add"])
    assert result == payload
    assert result[0]["Warnings"][0]["Details"] == "Title2 was merged into Title"


def test_success_residual_stderr_is_surfaced_not_dropped():
    """If the CLI writes a diagnostic to stderr on an exit-0 run, run_json
    surfaces it as _cli_warnings instead of silently dropping it (#256-3)."""
    runner = DirectCliRunner()
    with patch.object(
        runner, "run", return_value=_completed('{"Id": 1}', stderr="⚠ heads up")
    ):
        result = runner.run_json(["ads", "add"])
    assert result["Id"] == 1
    assert "heads up" in result["_cli_warnings"]


def test_success_empty_stderr_leaves_list_shape_intact():
    """The common case (empty stderr) must not reshape a list payload, so
    callers that index result[0] are unaffected (#256-3)."""
    payload = [{"Id": 1}, {"Id": 2}]
    runner = DirectCliRunner()
    with patch.object(runner, "run", return_value=_completed(json.dumps(payload))):
        result = runner.run_json(["ads", "get"])
    assert result == payload  # still a list, unwrapped


def test_tool_error_details_omitted_when_absent():
    """A ToolError with no details serializes without the key (byte-identical
    to the pre-#256 error dicts)."""
    payload = tool_error_dict(ToolError(error="x", message="m"))
    assert "details" not in payload


def test_tool_error_details_present_when_set():
    payload = tool_error_dict(ToolError(error="x", message="m", details="d"))
    assert payload["details"] == "d"


def test_cli_error_details_extracted_into_error_payload():
    """A CliError whose stderr carries 'Details: ...' surfaces those Details in
    the structured error dict via handle_cli_errors (#256-3)."""
    from server.cli.runner import CliError
    from server.tools.ads import ads_update

    err = CliError(
        "direct failed (exit 1): Error 8800: Ad not found. Details: adId=123",
        error_code=8800,
        stderr="Error 8800: Ad not found. Details: adId=123",
    )
    runner = mock_runner(None)
    runner.run_json.side_effect = err
    with patch("server.tools.ads.get_runner", return_value=runner):
        result = ads_update(id=BIG_AD_ID_STR, type="TEXT_AD", title="x")
    assert result["error"] == "not_found"
    assert result["details"] == "adId=123"


# --------------------------------------------------------------------------- #
# #4 — adimages_add uses a wider timeout.                                      #
# --------------------------------------------------------------------------- #


def test_adimages_add_uses_extended_timeout():
    """adimages_add must pass the extended timeout so large JPEGs do not hit the
    30 s default (#256-4)."""
    assert ADIMAGES_ADD_TIMEOUT_SECONDS > 30
    runner = mock_runner({"Id": 1})
    with patch("server.tools.images.get_runner", return_value=runner):
        adimages_add(name="img", image_data="base64data")
    _, kwargs = runner.run_json.call_args
    assert kwargs.get("timeout") == ADIMAGES_ADD_TIMEOUT_SECONDS
