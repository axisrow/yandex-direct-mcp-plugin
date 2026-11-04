"""Mock tests for the 28 audience_* tools (argv contract + guards).

The cassette layer covers the read paths against real `yac` stdout
(tests/test_audience_cassettes.py); this file pins the argv each tool builds
and the plugin-side guards. No network, no binary.
"""

from unittest.mock import patch

from server.tools.audience_accounts import audience_accounts_list
from server.tools.audience_delegates import (
    audience_delegates_add,
    audience_delegates_list,
    audience_delegates_remove,
)
from server.tools.audience_grants import (
    audience_grants_add,
    audience_grants_list,
    audience_grants_remove,
)
from server.tools.audience_pixels import (
    audience_pixels_create,
    audience_pixels_delete,
    audience_pixels_list,
    audience_pixels_undelete,
    audience_pixels_update,
)
from server.tools.audience_segments import (
    audience_segments_confirm,
    audience_segments_confirm_client_id,
    audience_segments_create_appmetrica,
    audience_segments_create_geo,
    audience_segments_create_geo_polygon,
    audience_segments_create_lookalike,
    audience_segments_create_metrika,
    audience_segments_create_pixel,
    audience_segments_delete,
    audience_segments_list,
    audience_segments_modify_data,
    audience_segments_reprocess,
    audience_segments_update,
    audience_segments_update_geo_points,
    audience_segments_upload_csv_file,
    audience_segments_upload_file,
)

SAMPLE: dict = {"segments": []}


def _run(module_name, tool, *args, **kwargs):
    """Call a tool with a mocked runner, returning (result, runner)."""
    from tests.helpers import mock_runner

    runner = mock_runner(SAMPLE)
    with patch(f"server.tools.{module_name}.get_audience_runner", return_value=runner):
        result = tool(*args, **kwargs)
    return result, runner


def _argv(runner):
    return runner.run_json.call_args[0][0]


# ── segments: read ────────────────────────────────────────────────────────


def test_segments_list_bare_argv():
    _, runner = _run("audience_segments", audience_segments_list)
    assert _argv(runner) == ["segments", "list"]


def test_segments_list_full_filters():
    _, runner = _run(
        "audience_segments", audience_segments_list, pixel=724143, limit=5, offset=10
    )
    assert _argv(runner) == [
        "segments",
        "list",
        "--pixel",
        "724143",
        "--limit",
        "5",
        "--offset",
        "10",
    ]


# ── segments: create family (data JSON passthrough) ──────────────────────


def test_segments_create_pixel_string_data():
    _, runner = _run(
        "audience_segments",
        audience_segments_create_pixel,
        '{"name": "seg", "pixel": 724143}',
    )
    assert _argv(runner) == [
        "segments",
        "create-pixel",
        "--data",
        '{"name": "seg", "pixel": 724143}',
    ]


def test_segments_create_pixel_accepts_parsed_dict():
    """MCP hosts may pre-parse the JSON string into a dict before the call."""
    _, runner = _run(
        "audience_segments", audience_segments_create_pixel, {"name": "seg"}
    )
    assert _argv(runner) == ["segments", "create-pixel", "--data", '{"name": "seg"}']


def test_segments_create_family_subcommands():
    cases = [
        (audience_segments_create_lookalike, "create-lookalike"),
        (audience_segments_create_metrika, "create-metrika"),
        (audience_segments_create_appmetrica, "create-appmetrica"),
        (audience_segments_create_geo, "create-geo"),
        (audience_segments_create_geo_polygon, "create-geo-polygon"),
    ]
    for tool, subcommand in cases:
        _, runner = _run("audience_segments", tool, '{"name": "seg"}')
        assert _argv(runner)[1] == subcommand


def test_segments_create_pixel_missing_data_is_guarded():
    result, runner = _run("audience_segments", audience_segments_create_pixel, "  ")
    assert result["error"] == "missing_data"
    runner.run_json.assert_not_called()


# ── segments: uploads ─────────────────────────────────────────────────────


def test_segments_upload_file_argv():
    _, runner = _run(
        "audience_segments", audience_segments_upload_file, "/tmp/data.txt"
    )
    assert _argv(runner) == ["segments", "upload-file", "/tmp/data.txt"]


def test_segments_upload_csv_file_argv():
    _, runner = _run(
        "audience_segments", audience_segments_upload_csv_file, "/tmp/data.csv"
    )
    assert _argv(runner) == ["segments", "upload-csv-file", "/tmp/data.csv"]


# ── segments: mutations with ids ──────────────────────────────────────────


def test_segments_update_geo_points():
    _, runner = _run(
        "audience_segments",
        audience_segments_update_geo_points,
        " 36644633 ",
        '[{"longitude": 37.6, "latitude": 55.7, "radius": 1000}]',
    )
    assert _argv(runner) == [
        "segments",
        "update-geo-points",
        "36644633",
        "--data",
        '[{"longitude": 37.6, "latitude": 55.7, "radius": 1000}]',
    ]


def test_segments_modify_data_tri_state_check_size():
    _, runner = _run(
        "audience_segments",
        audience_segments_modify_data,
        "12834430",
        "/tmp/data.txt",
        "addition",
        check_size=True,
    )
    assert _argv(runner) == [
        "segments",
        "modify-data",
        "12834430",
        "/tmp/data.txt",
        "--modification-type",
        "addition",
        "--check-size",
    ]
    _, runner = _run(
        "audience_segments",
        audience_segments_modify_data,
        "12834430",
        "/tmp/data.txt",
        "replace",
        check_size=False,
    )
    assert "--no-check-size" in _argv(runner)
    _, runner = _run(
        "audience_segments",
        audience_segments_modify_data,
        "12834430",
        "/tmp/data.txt",
        "subtraction",
    )
    assert "--check-size" not in _argv(runner)
    assert "--no-check-size" not in _argv(runner)


def test_segments_confirm_and_confirm_client_id():
    _, runner = _run(
        "audience_segments", audience_segments_confirm, "12834430", '{"name": "x"}'
    )
    assert _argv(runner) == [
        "segments",
        "confirm",
        "12834430",
        "--data",
        '{"name": "x"}',
    ]
    _, runner = _run(
        "audience_segments",
        audience_segments_confirm_client_id,
        " 12834430 ",
        '{"name": "x"}',
    )
    assert _argv(runner) == [
        "segments",
        "confirm-client-id",
        "12834430",
        "--data",
        '{"name": "x"}',
    ]


def test_segments_update_strips_id():
    _, runner = _run(
        "audience_segments", audience_segments_update, " 12834430 ", '{"name": "new"}'
    )
    assert _argv(runner) == [
        "segments",
        "update",
        "12834430",
        "--data",
        '{"name": "new"}',
    ]


def test_segments_delete_and_reprocess():
    _, runner = _run("audience_segments", audience_segments_delete, "12834430")
    assert _argv(runner) == ["segments", "delete", "12834430"]
    _, runner = _run("audience_segments", audience_segments_reprocess, "12834430")
    assert _argv(runner) == ["segments", "reprocess", "12834430"]


# ── grants ────────────────────────────────────────────────────────────────


def test_grants_list():
    _, runner = _run("audience_grants", audience_grants_list, "12834430")
    assert _argv(runner) == ["grants", "list", "12834430"]


def test_grants_add_minimal_and_full():
    _, runner = _run("audience_grants", audience_grants_add, "12834430", "someone")
    assert _argv(runner) == ["grants", "add", "12834430", "--user-login", "someone"]
    _, runner = _run(
        "audience_grants",
        audience_grants_add,
        "12834430",
        "someone",
        permission="view",
        comment="agency access",
    )
    assert _argv(runner) == [
        "grants",
        "add",
        "12834430",
        "--user-login",
        "someone",
        "--permission",
        "view",
        "--comment",
        "agency access",
    ]


def test_grants_remove():
    _, runner = _run("audience_grants", audience_grants_remove, "12834430", "someone")
    assert _argv(runner) == ["grants", "remove", "12834430", "--user-login", "someone"]


# ── pixels ────────────────────────────────────────────────────────────────


def test_pixels_list_and_create():
    _, runner = _run("audience_pixels", audience_pixels_list)
    assert _argv(runner) == ["pixels", "list"]
    _, runner = _run("audience_pixels", audience_pixels_create, "Pixel name")
    assert _argv(runner) == ["pixels", "create", "--name", "Pixel name"]


def test_pixels_update_delete_undelete():
    _, runner = _run("audience_pixels", audience_pixels_update, " 724143 ", "New name")
    assert _argv(runner) == ["pixels", "update", "724143", "--name", "New name"]
    _, runner = _run("audience_pixels", audience_pixels_delete, "724143")
    assert _argv(runner) == ["pixels", "delete", "724143"]
    _, runner = _run("audience_pixels", audience_pixels_undelete, "724143")
    assert _argv(runner) == ["pixels", "undelete", "724143"]


# ── accounts / delegates ──────────────────────────────────────────────────


def test_accounts_list():
    _, runner = _run("audience_accounts", audience_accounts_list)
    assert _argv(runner) == ["accounts", "list"]


def test_delegates_list_add_remove():
    _, runner = _run("audience_delegates", audience_delegates_list)
    assert _argv(runner) == ["delegates", "list"]
    _, runner = _run("audience_delegates", audience_delegates_add, "someone")
    assert _argv(runner) == ["delegates", "add", "--user-login", "someone"]
    _, runner = _run(
        "audience_delegates",
        audience_delegates_add,
        "someone",
        perm="edit",
        comment="ops",
    )
    assert _argv(runner) == [
        "delegates",
        "add",
        "--user-login",
        "someone",
        "--perm",
        "edit",
        "--comment",
        "ops",
    ]
    _, runner = _run("audience_delegates", audience_delegates_remove, "someone")
    assert _argv(runner) == ["delegates", "remove", "--user-login", "someone"]


# ── surface parity: all 28 contract names are implemented ────────────────


def test_all_audience_contract_names_are_implemented():
    from server.contract import AUDIENCE_SERVICE_METHODS
    from server.main import mcp

    registered = set(mcp._tool_manager._tools)
    expected = {
        f"audience_{service}_{method}"
        for service, methods in AUDIENCE_SERVICE_METHODS.items()
        for method in methods
    }
    missing = expected - registered
    assert not missing, f"audience tools not registered: {sorted(missing)}"


def test_audience_tools_expose_one_line_descriptions():
    """Progressive disclosure: short descriptions, full docs via tool_help."""
    from server.contract import AUDIENCE_TOOL_NAMES
    from server.main import mcp

    for name in AUDIENCE_TOOL_NAMES:
        tool = mcp._tool_manager._tools[name]
        description = tool.description or ""
        assert len(description) < 250, f"{name} description too long for startup budget"
