# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Code plugin for managing Yandex.Direct advertising campaigns. Wraps `direct` CLI (Python) via an MCP server with OAuth 2.0 token management.

**Status:** Implemented.

## Architecture

```
direct (Python CLI)         — talks to Yandex.Direct API
       ↑
server/main.py (MCP)        — FastMCP server (stdio transport)
       ↑
server/auth/                — OAuth 2.0 module (httpx)
server/cli/runner.py        — subprocess wrapper over `direct`
server/tools/               — 8 MCP tools (campaigns, ads, keywords, reports, auth)
       ↑
skills/                     — domain knowledge (SKILL.md files)
       ↑
.claude-plugin/plugin.json  — plugin manifest
.mcp.json                   — MCP server config
```

## Tech Stack

- **Python >= 3.11**, no Node.js
- **mcp** (PyPI) for MCP server, **httpx** for OAuth HTTP calls
- **pytest** with cassette-based testing, `unittest.mock` for edge cases
- **ruff** for linting, **mypy** for type checking
- **pyproject.toml** (PEP 621) for build config

## Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Install with docs support
pip install -e ".[dev,docs]"

# Run all tests (cassette-based, no API token needed)
pytest

# Run only mock-based edge case tests
pytest -m mocks

# Run integration tests (requires live OAuth token)
pytest -m integration

# Record cassettes from live API
pytest --record

# Sanitize recorded cassettes
python -m tests.sanitize

# Audit cassettes for leaked secrets
python -m tests.audit

# Interactive OAuth token setup
python -m tests.setup

# Lint
ruff check .
ruff format .

# Type check
mypy .

# Build docs
cd docs && make html
```

## Project Structure

```
yandex-direct-mcp-plugin/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── .mcp.json                    # MCP server configuration
├── .pre-commit-config.yaml      # Pre-commit hooks
├── pyproject.toml               # Dependencies and build config
├── server/
│   ├── main.py                  # FastMCP entry point (stdio)
│   ├── auth/
│   │   ├── storage.py           # FileTokenStorage + TokenData
│   │   └── oauth.py             # OAuthManager (exchange, refresh, status)
│   ├── cli/
│   │   └── runner.py            # DirectCliRunner (subprocess wrapper)
│   └── tools/
│       ├── __init__.py          # ToolError dataclass
│       ├── campaigns.py         # campaigns_list, campaigns_update
│       ├── ads.py               # ads_list
│       ├── keywords.py          # keywords_list, keywords_update
│       ├── reports.py           # reports_get
│       └── auth_tools.py        # auth_status, auth_setup
├── skills/
│   ├── yandex-direct/SKILL.md   # Campaign management skill
│   └── direct-ads/SKILL.md      # Ad copywriting skill
├── tests/
│   ├── conftest.py              # Pytest fixtures, cli_recorder setup
│   ├── cli_recorder.py          # Cassette record/replay
│   ├── sanitize.py              # Strip secrets from cassettes
│   ├── audit.py                 # Detect leaked data
│   ├── setup.py                 # Interactive OAuth setup
│   ├── recordings/              # Recorded cassettes (committed)
│   └── fixtures/                # Test data
├── docs/                        # Sphinx documentation
└── .github/workflows/           # CI/CD pipelines
```

## MCP Tools (8 total)

| Tool | Purpose |
|---|---|
| `campaigns_list` | List campaigns, optional state filter |
| `campaigns_update` | Enable/disable campaign |
| `ads_list` | List ads by campaign IDs |
| `keywords_list` | List keywords by campaign IDs |
| `keywords_update` | Update keyword bid (in micro-units: 15 RUB = 15000000) |
| `reports_get` | Campaign statistics for date range |
| `auth_status` | Check OAuth token validity |
| `auth_setup` | Submit 7-digit authorization code |

## Testing Model

Three test modes:
1. **Cassettes** (default `pytest`) — recorded CLI responses in `tests/recordings/`, no network needed
2. **Mocks** (`pytest -m mocks`) — `unittest.mock.patch("subprocess.run")` for unreproducible edge cases
3. **Integration** (`pytest -m integration`) — live API, requires OAuth token

Cassette lifecycle: record → sanitize (strip secrets/commercial data) → commit → replay in tests. Audit script blocks commits containing leaked tokens or PII.

## Domain Notes

- Bids use micro-units: 15 RUB = 15,000,000
- API batch limit: max 10 IDs per request
- Campaign IDs ~73-77M range belong to a second account (foreign_campaign error)
- OAuth tokens stored in `${CLAUDE_PLUGIN_DATA}/tokens.json` (gitignored)
- CLI binary: `direct` (installed via `pip install direct-cli`)
- Language: project docs in Russian, code identifiers in English
