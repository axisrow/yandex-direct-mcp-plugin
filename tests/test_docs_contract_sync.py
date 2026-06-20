"""CLAUDE.md is the declared canonical source of truth for tool names, but it has
no guard against drifting from the live contract (issue #242). This cross-checks
the doc tables against ``server.contract`` so a newly registered tool (or a
renamed/removed one) cannot silently go undocumented.
"""

import re
from pathlib import Path

from server.contract import (
    CLI_HELPER_TOOL_NAMES,
    DIRECT_API_TOOL_NAMES,
    PLUGIN_ONLY_TOOL_NAMES,
    PUBLIC_TOOL_NAMES,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"

# Files that CLAUDE.md once listed as orphaned modules in server/tools/ but which
# have since been deleted from disk — the doc must not claim they still exist.
_REMOVED_ORPHAN_FILES = (
    "dynamic_targets.py",
    "smart_targets.py",
    "negative_keywords.py",
)


def _section(text: str, heading: str) -> str:
    assert heading in text, f"CLAUDE.md is missing the heading: {heading!r}"
    start = text.index(heading)
    nxt = text.find("\n### ", start + len(heading))
    return text[start : nxt if nxt != -1 else len(text)]


def _heading_count(section: str) -> int:
    # Anchor (N) at end-of-heading so a future "### X (v2) (139)" can't match the
    # wrong group.
    line = section.splitlines()[0]
    match = re.search(r"\((\d+)\)$", line)
    assert match, f"section heading has no trailing (N) count: {line!r}"
    return int(match.group(1))


def _row_names(section: str) -> list[str]:
    # Parse only the first Markdown table in the section: a table ends at the
    # first non-pipe line after its body. Sturdier than keying off a trailing
    # sub-table's header word — e.g. the Plugin section's "| Prompt |" table,
    # whose oauth_login row must NOT be counted as a tool.
    names: list[str] = []
    in_table = False
    for line in section.splitlines():
        if line.startswith("|"):
            in_table = True
            match = re.match(r"\| `([a-z0-9_]+)` \|", line)
            if match:
                names.append(match.group(1))
        elif in_table:
            break
    return names


def _check(heading: str, contract_names: frozenset[str]) -> None:
    section = _section(CLAUDE_MD.read_text(), heading)
    rows = _row_names(section)
    documented = set(rows)

    assert len(rows) == len(documented), (
        f"{heading!r}: duplicate tool rows: "
        f"{sorted(n for n in documented if rows.count(n) > 1)}"
    )
    missing = sorted(contract_names - documented)
    extra = sorted(documented - contract_names)
    assert not missing, f"{heading!r}: tools in contract but undocumented: {missing}"
    assert not extra, f"{heading!r}: documented tools not in contract: {extra}"
    count = _heading_count(section)
    assert count == len(contract_names), (
        f"{heading!r}: heading count {count} != {len(contract_names)} contract tools"
    )


def test_direct_api_table_matches_contract() -> None:
    _check("### Direct API tools", DIRECT_API_TOOL_NAMES)


def test_cli_helper_table_matches_contract() -> None:
    _check("### CLI helper tools", CLI_HELPER_TOOL_NAMES)


def test_plugin_table_matches_contract() -> None:
    _check("### Plugin tools", PLUGIN_ONLY_TOOL_NAMES)


def test_mcp_tools_headline_total_matches_contract() -> None:
    """The most-read count — ``## MCP Tools (N total)`` — must track the contract
    so the hardcoded total (the only one not under any test) cannot go stale."""
    text = CLAUDE_MD.read_text()
    match = re.search(r"^## MCP Tools \((\d+) total\)", text, re.MULTILINE)
    assert match, "CLAUDE.md is missing the '## MCP Tools (N total)' headline"
    assert int(match.group(1)) == len(PUBLIC_TOOL_NAMES), (
        f"headline total {match.group(1)} != {len(PUBLIC_TOOL_NAMES)} contract tools"
    )


def test_no_stale_orphan_file_references() -> None:
    text = CLAUDE_MD.read_text()
    for name in _REMOVED_ORPHAN_FILES:
        assert (REPO_ROOT / "server" / "tools" / name).exists() is False, (
            f"{name} unexpectedly exists on disk"
        )
        assert name not in text, (
            f"CLAUDE.md still references removed orphan file {name!r}"
        )
