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
server/tools/               — 79 MCP tools across 27 modules
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

# Run a single test
pytest tests/test_campaigns.py::test_campaigns_list -v

# Run only mock-based edge case tests
pytest -m mocks

# Run integration tests (requires .env.test with YANDEX_OAUTH_TOKEN)
pytest -m integration

# Record cassettes from live API
pytest --record

# Sanitize recorded cassettes
python -m tests.sanitize

# Audit cassettes for leaked secrets
python -m tests.audit

# Interactive OAuth token setup
python -m tests.setup

# Run MCP server directly (for local testing)
python3 server/main.py

# Lint
ruff check .
ruff format .

# Type check
mypy .

# Build docs
cd docs && make html
```

## Environment Variables

## Authentication

Four methods, from simplest to advanced:

### 1. Environment variable (recommended)

Add to `~/.claude/settings.json`:
```json
{
  "env": {
    "YANDEX_DIRECT_TOKEN": "y0_..."
  }
}
```
Restart Claude Code. Done.

### 2. Plugin settings

Set `token` in plugin config — it arrives as `CLAUDE_PLUGIN_OPTION_token`.

### 3. OAuth PKCE (interactive, no secrets)

Run `auth_login` (interactive, uses elicitation) or `auth_setup` (manual code entry). Uses built-in OAuth app, no `client_secret` needed. Token is saved to disk and auto-refreshed.

### 4. Custom OAuth app (advanced)

Set `client_id` + `client_secret` in plugin settings for your own registered Yandex app. Disables PKCE, uses classic OAuth flow.

### Priority

`YANDEX_DIRECT_TOKEN` > `CLAUDE_PLUGIN_OPTION_token` > stored OAuth token (auto-refresh).

### Environment variables

- `YANDEX_DIRECT_TOKEN` — direct OAuth token (highest priority)
- `CLAUDE_PLUGIN_DATA` — directory for `tokens.json` storage
- `CLAUDE_PLUGIN_OPTION_token` — token via plugin settings
- `CLAUDE_PLUGIN_OPTION_client_id` — custom OAuth app client ID
- `CLAUDE_PLUGIN_OPTION_client_secret` — custom OAuth app secret (disables PKCE)

Integration tests: copy `.env.test.example` → `.env.test` and fill `YANDEX_OAUTH_TOKEN`, `YANDEX_CLIENT_ID`, `YANDEX_CLIENT_SECRET`, `YANDEX_LOGIN`.

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
│       ├── __init__.py          # ToolError dataclass, handle_cli_errors, get_runner
│       ├── helpers.py           # Shared validation (parse_ids, check_batch_limit)
│       ├── adextensions.py      # adextensions_list/add/delete
│       ├── adgroups.py          # adgroups_list/add/update/delete
│       ├── ads.py               # ads_list/add/update/delete/moderate/suspend/resume
│       ├── images.py            # adimages_list/add/delete
│       ├── agency.py            # agency_clients_list/add/delete
│       ├── audience.py          # audience_targets_list/add/delete/suspend/resume
│       ├── auth_tools.py        # auth_status, auth_setup, auth_login
│       ├── bids.py              # bids_list/set
│       ├── bidmodifiers.py      # bidmodifiers_list/set/toggle/delete
│       ├── campaigns.py         # campaigns_list/update/add/delete/archive/unarchive
│       ├── changes.py           # changes_check/checkcamp/checkdict
│       ├── clients.py           # clients_get/update
│       ├── creatives.py         # creatives_list
│       ├── dictionaries.py      # dictionaries_get
│       ├── dynamic_targets.py   # dynamic_targets_list/add/update/delete
│       ├── feeds.py             # feeds_list/add/update/delete
│       ├── keywords.py          # keywords_list/update/add/delete/suspend/resume
│       ├── leads.py             # leads_list
│       ├── negative_keyword_shared_sets.py # negative_keyword_shared_sets_list/add/update/delete
│       ├── negative_keywords.py # negative_keywords_list/add/update/delete
│       ├── reports.py           # reports_get
│       ├── research.py          # keywords_has_volume/deduplicate
│       ├── retargeting.py       # retargeting_list/add/delete
│       ├── sitelinks.py         # sitelinks_list/add/delete
│       ├── smart_targets.py     # smart_targets_list/add/update/delete
│       ├── turbo_pages.py       # turbo_pages_list
│       └── vcards.py            # vcards_list/add/delete
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

## MCP Tools (79 total) + 1 Prompt

| Tool | Purpose |
|---|---|
| `campaigns_list` | List campaigns, optional state filter |
| `campaigns_update` | Enable/disable campaign |
| `campaigns_add` | Create campaign |
| `campaigns_delete` | Delete campaigns |
| `campaigns_archive` | Archive campaigns |
| `campaigns_unarchive` | Unarchive campaigns |
| `adgroups_list` | List ad groups |
| `adgroups_add` | Create ad group |
| `adgroups_update` | Update ad group |
| `adgroups_delete` | Delete ad groups |
| `ads_list` | List ads by campaign IDs |
| `ads_add` | Create ad |
| `ads_update` | Update ad |
| `ads_delete` | Delete ads |
| `ads_moderate` | Submit ads for moderation |
| `ads_suspend` | Suspend ads |
| `ads_resume` | Resume suspended ads |
| `keywords_list` | List keywords by campaign IDs |
| `keywords_update` | Update keyword bid (micro-units) |
| `keywords_add` | Add keywords |
| `keywords_delete` | Delete keywords |
| `keywords_suspend` | Suspend keywords |
| `keywords_resume` | Resume keywords |
| `bids_list` | List bids |
| `bids_set` | Set bid for campaign |
| `bidmodifiers_list` | List bid modifiers |
| `bidmodifiers_set` | Set bid modifier |
| `bidmodifiers_toggle` | Toggle modifier on/off |
| `bidmodifiers_delete` | Delete bid modifiers |
| `sitelinks_list` | List sitelinks sets |
| `sitelinks_add` | Add sitelinks set |
| `sitelinks_delete` | Delete sitelinks |
| `vcards_list` | List vCards |
| `vcards_add` | Add vCard |
| `vcards_delete` | Delete vCards |
| `adimages_list` | List ad images |
| `adimages_add` | Add ad image |
| `adimages_delete` | Delete images |
| `adextensions_list` | List ad extensions |
| `adextensions_add` | Add extension |
| `adextensions_delete` | Delete extensions |
| `audience_targets_list` | List audience targets |
| `audience_targets_add` | Add audience target |
| `audience_targets_delete` | Delete targets |
| `audience_targets_suspend` | Suspend targets |
| `audience_targets_resume` | Resume targets |
| `retargeting_list` | List retargeting lists |
| `retargeting_add` | Add retargeting list |
| `retargeting_delete` | Delete retargeting lists |
| `dynamic_targets_list` | List dynamic targets |
| `dynamic_targets_add` | Add dynamic target |
| `dynamic_targets_update` | Update dynamic target |
| `dynamic_targets_delete` | Delete dynamic targets |
| `negative_keywords_list` | List negative keywords |
| `negative_keywords_add` | Add negative keywords |
| `negative_keywords_update` | Update negative keywords |
| `negative_keywords_delete` | Delete negative keywords |
| `negative_keyword_shared_sets_list` | List negative keyword shared sets |
| `negative_keyword_shared_sets_add` | Add negative keyword shared set |
| `negative_keyword_shared_sets_update` | Update negative keyword shared set |
| `negative_keyword_shared_sets_delete` | Delete negative keyword shared set |
| `smart_targets_list` | List smart targets |
| `smart_targets_add` | Add smart target |
| `smart_targets_update` | Update smart target |
| `smart_targets_delete` | Delete smart targets |
| `dictionaries_get` | Get dictionary data |
| `changes_check` | Check changes since timestamp |
| `changes_checkcamp` | Check campaign changes |
| `changes_checkdict` | Check dictionary changes |
| `clients_get` | Get client info |
| `clients_update` | Update client |
| `agency_clients_list` | List agency clients |
| `agency_clients_add` | Add client to agency |
| `agency_clients_delete` | Remove client from agency |
| `keywords_has_volume` | Check keyword search volume |
| `keywords_deduplicate` | Deduplicate keywords |
| `leads_list` | List leads |
| `feeds_list` | List feeds |
| `feeds_add` | Add feed |
| `feeds_update` | Update feed |
| `feeds_delete` | Delete feeds |
| `creatives_list` | List creatives |
| `turbo_pages_list` | List turbo pages |
| `reports_get` | Campaign statistics for date range |
| `auth_status` | Check OAuth token validity |
| `auth_setup` | Submit authorization code or direct token |
| `auth_login` | Interactive OAuth flow with elicitation |

| Prompt | Purpose |
|---|---|
| `oauth_login` | Start OAuth PKCE authorization flow |

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
