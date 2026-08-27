"""Regression guard for the MCP tool-spec token budget (#149).

The tool spec (name + description + JSON Schema of every tool) is a fixed cost
paid on every request while the plugin is connected. 0.3.0 cut it sharply by
moving full docstrings to ``tool_help`` and grouping campaign strategy params.
This guard fails when the budget silently balloons back — e.g. someone re-adds
long descriptions or a wide flat parameter matrix — so the regression is caught
in CI instead of in users' context windows.

Measurement reuses ``tests.measure_tool_tokens`` but forces the dependency-free
``len/4`` estimate so the numbers are deterministic regardless of whether
tiktoken happens to be installed in the test environment.

Ceilings are snapshots with headroom, not exact values. A legitimate increase
(new tools, richer schemas) should bump the ceiling here AND update
``docs/token-budget.md`` in the same PR — that is the intended, explicit knob.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from server.contract import DEFAULT_TOOL_NAMES, PUBLIC_TOOL_NAMES

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_OPTIONAL_TOOLS = "YANDEX_DIRECT_OPTIONAL_TOOLS"
_TOOL_SURFACE_ENV = (
    ENV_OPTIONAL_TOOLS,
    "YANDEX_DIRECT_TOOL_PROFILE",
    "YANDEX_DIRECT_ENABLED_GROUPS",
    "YANDEX_DIRECT_DISABLED_GROUPS",
    "YANDEX_DIRECT_ENABLED_TOOLS",
    "YANDEX_DIRECT_DISABLED_TOOLS",
)
_ALL_OPTIONAL_MODULE_FILES = tuple(
    PROJECT_ROOT / "server" / "tools" / f"{name}.py"
    for name in ("masters", "history", "playwright", "trackingparams")
)

# Snapshot under approx(len/4) as of 2026-08-27 (see docs/token-budget.md):
#   total ≈ 33,156 · descriptions ≈ 5,313 · 149 default tools.
# Lowered 38,000 → 35,500 (#220-A, ads dicts) → 33,500 (#220-B, campaigns dicts).
# Ceilings carry headroom to absorb small additions but stay well below a
# regression (re-adding full docstrings alone was ~16k of descriptions).
DEFAULT_TOTAL_TOKEN_CEILING = 33_500
FULL_TOTAL_TOKEN_CEILING = 36_500
DESCRIPTION_TOKEN_CEILING = 7_000


def _measure(env: dict[str, str] | None = None) -> dict:
    """Measure one surface in a fresh interpreter to isolate import side effects."""
    proc_env = os.environ.copy()
    for name in _TOOL_SURFACE_ENV:
        proc_env.pop(name, None)
    if env:
        proc_env.update(env)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tests.measure_tool_tokens",
            "--json",
            "--approx",
        ],
        cwd=PROJECT_ROOT,
        env=proc_env,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    measured = json.loads(result.stdout)
    assert measured["method"] == "approx(len/4)"
    return measured


def test_total_tool_spec_budget_under_ceiling() -> None:
    s = _measure()
    assert s["n_tools"] == len(DEFAULT_TOOL_NAMES)
    assert s["total_tok"] <= DEFAULT_TOTAL_TOKEN_CEILING, (
        f"tool-spec budget {s['total_tok']:,} exceeds ceiling "
        f"{DEFAULT_TOTAL_TOKEN_CEILING:,} ({s['method']}). If this growth is intended, "
        "update docs/token-budget.md and raise DEFAULT_TOTAL_TOKEN_CEILING in the same PR."
    )


@pytest.mark.skipif(
    not all(path.exists() for path in _ALL_OPTIONAL_MODULE_FILES),
    reason="full optional tool implementations land in later #290 work items",
)
def test_full_tool_spec_budget_under_ceiling() -> None:
    s = _measure({ENV_OPTIONAL_TOOLS: "all"})
    assert s["n_tools"] == len(PUBLIC_TOOL_NAMES)
    assert s["total_tok"] <= FULL_TOTAL_TOKEN_CEILING, (
        f"full tool-spec budget {s['total_tok']:,} exceeds ceiling "
        f"{FULL_TOTAL_TOKEN_CEILING:,} ({s['method']}). If this growth is intended, "
        "update docs/token-budget.md and FULL_TOTAL_TOKEN_CEILING in the same PR."
    )


def test_descriptions_stay_compressed() -> None:
    """Protect the 0.3.0 progressive-disclosure win (descriptions ≪ docstrings)."""
    s = _measure()
    assert s["total_desc_tok"] <= DESCRIPTION_TOKEN_CEILING, (
        f"tool descriptions total {s['total_desc_tok']:,} tokens, over ceiling "
        f"{DESCRIPTION_TOKEN_CEILING:,}. Full docs belong in tool_help, not in "
        "the one-line description. If intended, bump the ceiling + docs."
    )
