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

import asyncio

from unittest.mock import patch

import tests.measure_tool_tokens as mtt

# Deterministic, tokenizer-independent estimate (≈4 chars/token).
_APPROX_COUNTER = ((lambda s: (len(s or "") + 3) // 4), "approx(len/4)")

# Snapshot under approx(len/4) as of 2026-06-16 (see docs/token-budget.md):
#   total ≈ 34,744 · descriptions ≈ 5,157 · 146 tools.
# Ceilings carry headroom to absorb small additions but stay well below a
# regression (re-adding full docstrings alone was ~16k of descriptions).
TOTAL_TOKEN_CEILING = 38_000
DESCRIPTION_TOKEN_CEILING = 7_000


def _measure():
    with patch.object(mtt, "_make_counter", lambda: _APPROX_COUNTER):
        rows, method = asyncio.run(mtt.collect_rows())
    return mtt.summarize(rows, method)


def test_total_tool_spec_budget_under_ceiling() -> None:
    s = _measure()
    assert s["total_tok"] <= TOTAL_TOKEN_CEILING, (
        f"tool-spec budget {s['total_tok']:,} exceeds ceiling "
        f"{TOTAL_TOKEN_CEILING:,} ({s['method']}). If this growth is intended, "
        "update docs/token-budget.md and raise TOTAL_TOKEN_CEILING in the same PR."
    )


def test_descriptions_stay_compressed() -> None:
    """Protect the 0.3.0 progressive-disclosure win (descriptions ≪ docstrings)."""
    s = _measure()
    assert s["total_desc_tok"] <= DESCRIPTION_TOKEN_CEILING, (
        f"tool descriptions total {s['total_desc_tok']:,} tokens, over ceiling "
        f"{DESCRIPTION_TOKEN_CEILING:,}. Full docs belong in tool_help, not in "
        "the one-line description. If intended, bump the ceiling + docs."
    )
