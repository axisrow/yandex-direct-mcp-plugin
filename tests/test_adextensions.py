"""Argv-composition guard for adextensions_get (#237 cluster A).

adextensions had no dedicated test file; this pins the emitted argv now that the
scalar filters are driven by ADEXTENSION_GET_OPTIONS via append_cli_options.
"""

from unittest.mock import patch

from server.tools.adextensions import adextensions_list
from tests.helpers import mock_runner


def _capture_argv(**kwargs):
    runner = mock_runner([])
    with patch("server.tools.adextensions.get_runner", return_value=runner):
        adextensions_list(**kwargs)
    return runner.run_json.call_args[0][0]


def test_adextensions_get_argv_composition():
    argv = _capture_argv(
        ids="1,2",
        types=" T ",
        states="ST",
        statuses="STA",
        modified_since="2026-01-01",
        limit=10,
        fetch_all=True,
        fields="Id",
        callout_field_names="CalloutText",
    )
    assert argv == [
        "adextensions",
        "get",
        "--format",
        "json",
        "--ids",
        "1,2",
        "--types",
        "T",
        "--states",
        "ST",
        "--statuses",
        "STA",
        "--modified-since",
        "2026-01-01",
        "--limit",
        "10",
        "--fetch-all",
        "--fields",
        "Id",
        "--callout-field-names",
        "CalloutText",
    ]


def test_adextensions_get_omits_unset_filters():
    argv = _capture_argv(ids="5")
    assert argv == ["adextensions", "get", "--format", "json", "--ids", "5"]
