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
server/contract.py          — machine-readable parity layer (124 tools)
server/auth/                — OAuth 2.0 module (httpx)
server/cli/runner.py        — subprocess wrapper over `direct`
server/tools/               — 124 MCP tools across 33 active modules
       ↑
skills/                     — domain knowledge (SKILL.md files)
       ↑
.claude-plugin/plugin.json  — plugin manifest
.mcp.json                   — MCP server config
```

### Contract hierarchy

```
MCP → direct → tapi-yandex-direct → Yandex.Direct API
```

- MCP **never** calls Yandex.Direct directly.
- `direct` is the only execution/transport boundary.
- `tapi-yandex-direct` naming is the default source reused by the CLI.
- WSDL / Reports spec wins when CLI convenience names drift.

The machine-readable parity source is `server/contract.py`
(`PUBLIC_CONTRACT`, `TRANSPORT_BLOCKED_OPERATIONS`, `RENAMED_TOOL_MIGRATION`).

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
│   ├── contract.py              # Machine-readable parity (PUBLIC_CONTRACT, TRANSPORT_BLOCKED_OPERATIONS, RENAMED_TOOL_MIGRATION)
│   ├── auth/
│   │   ├── storage.py           # FileTokenStorage + TokenData
│   │   └── oauth.py             # OAuthManager (exchange, refresh, status)
│   ├── cli/
│   │   └── runner.py            # DirectCliRunner (subprocess wrapper)
│   └── tools/
│       ├── __init__.py          # ToolError dataclass, handle_cli_errors, get_runner
│       ├── helpers.py           # Shared validation (parse_ids, check_batch_limit)
│       ├── adextensions.py      # adextensions_get/add/delete
│       ├── adgroups.py          # adgroups_get/add/update/delete
│       ├── ads.py               # ads_get/add/update/delete/moderate/suspend/resume/archive/unarchive
│       ├── advideos.py          # advideos_get/add
│       ├── images.py            # adimages_get/add/delete
│       ├── agency.py            # agencyclients_get/add/update/delete + add_passport_organization[_member]
│       ├── audience.py          # audiencetargets_get/add/delete/suspend/resume/set_bids
│       ├── auth_tools.py        # auth_status, auth_setup, auth_login
│       ├── bids.py              # bids_get/set/set_auto
│       ├── businesses.py        # businesses_get
│       ├── keyword_bids.py      # keywordbids_get/set/set_auto
│       ├── bidmodifiers.py      # bidmodifiers_get/add/set/delete/toggle
│       ├── campaigns.py         # campaigns_get/update/add/delete/archive/unarchive/suspend/resume
│       ├── changes.py           # changes_check/check_campaigns/check_dictionaries
│       ├── clients.py           # clients_get/update
│       ├── creatives.py         # creatives_get/add
│       ├── dictionaries.py      # dictionaries_get/get_geo_regions/list_names
│       ├── dynamic_ads.py       # dynamicads_get/add/delete/suspend/resume/set_bids (update transport-blocked)
│       ├── feeds.py             # feeds_get/add/update/delete
│       ├── keywords.py          # keywords_get/update/add/delete/suspend/resume/archive/unarchive
│       ├── leads.py             # leads_get
│       ├── negative_keyword_shared_sets.py  # negativekeywordsharedsets_get/add/update/delete
│       ├── reports.py           # reports_get/list_types
│       ├── research.py          # keywordsresearch_has_search_volume/deduplicate
│       ├── retargeting.py       # retargeting_get/add/update/delete
│       ├── sitelinks.py         # sitelinks_get/add/delete
│       ├── smart_ad_targets.py  # smartadtargets_get/add/update/delete/suspend/resume/set_bids
│       ├── turbo_pages.py       # turbopages_get
│       └── vcards.py            # vcards_get/add/delete
│   # Orphaned (not imported — kept for git history):
│   #   dynamic_targets.py, smart_targets.py, negative_keywords.py
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

## MCP Tools (124 total) + 1 Prompt

The canonical source of truth for tool names is `server/contract.py`.
Naming follows `service_method` from `tapi-yandex-direct`/`direct-cli`;
WSDL/reports spec wins when there is drift.

### Direct API tools (118)

| Tool | Purpose |
|---|---|
| `campaigns_get` | List campaigns, optional state/status/type filter |
| `campaigns_update` | Update campaign fields |
| `campaigns_add` | Create campaign |
| `campaigns_delete` | Delete campaigns |
| `campaigns_archive` | Archive campaigns |
| `campaigns_unarchive` | Unarchive campaigns |
| `campaigns_suspend` | Suspend campaigns |
| `campaigns_resume` | Resume campaigns |
| `adgroups_get` | List ad groups |
| `adgroups_add` | Create ad group |
| `adgroups_update` | Update ad group |
| `adgroups_delete` | Delete ad groups |
| `ads_get` | List ads by campaign IDs |
| `ads_add` | Create ad |
| `ads_update` | Update ad |
| `ads_delete` | Delete ads |
| `ads_moderate` | Submit ads for moderation |
| `ads_suspend` | Suspend ads |
| `ads_resume` | Resume suspended ads |
| `ads_archive` | Archive ads |
| `ads_unarchive` | Unarchive ads |
| `advideos_get` | List ad videos |
| `advideos_add` | Add ad video (url or video_data) |
| `adimages_get` | List ad images |
| `adimages_add` | Add ad image |
| `adimages_delete` | Delete images |
| `adextensions_get` | List ad extensions |
| `adextensions_add` | Add extension |
| `adextensions_delete` | Delete extensions |
| `keywords_get` | List keywords by campaign IDs |
| `keywords_update` | Update keyword text or user params (use `keyword_bids_set` for bids) |
| `keywords_add` | Add keywords |
| `keywords_delete` | Delete keywords |
| `keywords_suspend` | Suspend keywords |
| `keywords_resume` | Resume keywords |
| `keywords_archive` | Archive keywords |
| `keywords_unarchive` | Unarchive keywords |
| `keywordbids_get` | List keyword bids |
| `keywordbids_set` | Set keyword bids |
| `keywordbids_set_auto` | Set keyword bids to auto strategy |
| `bids_get` | List bids |
| `bids_set` | Set bid for campaign |
| `bids_set_auto` | Set bids to auto strategy |
| `bidmodifiers_get` | List bid modifiers |
| `bidmodifiers_add` | Add bid modifier |
| `bidmodifiers_set` | Update existing bid modifier by `id` (use `bidmodifiers_add` to create) |
| `bidmodifiers_delete` | Delete bid modifiers |
| `sitelinks_get` | List sitelinks sets |
| `sitelinks_add` | Add sitelinks set |
| `sitelinks_delete` | Delete sitelinks |
| `vcards_get` | List vCards |
| `vcards_add` | Add vCard |
| `vcards_delete` | Delete vCards |
| `audiencetargets_get` | List audience targets |
| `audiencetargets_add` | Add audience target |
| `audiencetargets_delete` | Delete targets |
| `audiencetargets_suspend` | Suspend targets |
| `audiencetargets_resume` | Resume targets |
| `audiencetargets_set_bids` | Set bids for audience targets |
| `retargeting_get` | List retargeting lists |
| `retargeting_add` | Add retargeting list |
| `retargeting_update` | Update retargeting list |
| `retargeting_delete` | Delete retargeting lists |
| `dynamicads_get` | List dynamic ad targets (webpages) |
| `dynamicads_add` | Add dynamic ad target |
| `dynamicads_delete` | Delete dynamic ad targets |
| `dynamicads_suspend` | Suspend dynamic ad targets |
| `dynamicads_resume` | Resume dynamic ad targets |
| `dynamicads_set_bids` | Set bids for dynamic ad targets |
| `dynamicfeedadtargets_get` | List dynamic feed ad targets |
| `dynamicfeedadtargets_add` | Add dynamic feed ad target |
| `dynamicfeedadtargets_delete` | Delete dynamic feed ad target |
| `dynamicfeedadtargets_suspend` | Suspend dynamic feed ad targets |
| `dynamicfeedadtargets_resume` | Resume dynamic feed ad targets |
| `dynamicfeedadtargets_set_bids` | Set bids for dynamic feed ad targets |
| `smartadtargets_get` | List smart ad targets |
| `smartadtargets_add` | Add smart ad target |
| `smartadtargets_update` | Update smart ad target |
| `smartadtargets_delete` | Delete smart ad targets |
| `smartadtargets_suspend` | Suspend smart ad targets |
| `smartadtargets_resume` | Resume smart ad targets |
| `smartadtargets_set_bids` | Set bids for smart ad targets |
| `strategies_get` | List bidding strategies |
| `strategies_add` | Add bidding strategy |
| `strategies_update` | Update bidding strategy |
| `strategies_archive` | Archive bidding strategy |
| `strategies_unarchive` | Unarchive bidding strategy |
| `negativekeywordsharedsets_get` | List negative keyword shared sets |
| `negativekeywordsharedsets_add` | Add negative keyword shared set |
| `negativekeywordsharedsets_update` | Update negative keyword shared set |
| `negativekeywordsharedsets_delete` | Delete negative keyword shared set |
| `agencyclients_get` | List agency clients |
| `agencyclients_add` | Add client to agency |
| `agencyclients_update` | Update agency client |
| `agencyclients_add_passport_organization` | Add agency client backed by Passport org |
| `agencyclients_add_passport_organization_member` | Invite user to Passport org client |
| `businesses_get` | List businesses |
| `dictionaries_get` | Get dictionary data |
| `dictionaries_get_geo_regions` | Get geo regions dictionary |
| `changes_check` | Check changes since timestamp |
| `changes_check_campaigns` | Check campaign changes |
| `changes_check_dictionaries` | Check dictionary changes |
| `clients_get` | Get client info |
| `clients_update` | Update client |
| `keywordsresearch_has_search_volume` | Check keyword search volume |
| `keywordsresearch_deduplicate` | Deduplicate keywords |
| `leads_get` | List leads |
| `feeds_get` | List feeds |
| `feeds_add` | Add feed |
| `feeds_update` | Update feed |
| `feeds_delete` | Delete feeds |
| `creatives_get` | List creatives |
| `creatives_add` | Add creative |
| `turbopages_get` | List turbo pages |
| `reports_get` | Campaign statistics for date range |

### CLI helper tools (3)

These are public but explicitly not 1:1 Direct API methods.

| Tool | Purpose |
|---|---|
| `agencyclients_delete` | Remove client from agency (no API backing) |
| `dictionaries_list_names` | List available dictionary names |
| `reports_list_types` | List available report types |

### Plugin tools (3)

Auth/utility tools unrelated to Direct API parity.

| Tool | Purpose |
|---|---|
| `auth_status` | Check OAuth token validity |
| `auth_setup` | Submit authorization code or direct token |
| `auth_login` | Interactive OAuth flow with elicitation |

| Prompt | Purpose |
|---|---|
| `oauth_login` | Start OAuth PKCE authorization flow |

### Transport-blocked operations

Operations in the WSDL/tapi surface that have no `direct-cli` subcommand.
See `server/contract.py` → `TRANSPORT_BLOCKED_OPERATIONS` for details.

| Operation | Reason |
|---|---|
| `dynamicads_update` | `direct dynamicads update` subcommand does not exist in CLI |
| `negativekeywords_*` | `negativekeywords` is not a CLI service; use AdGroups payload or `negativekeywordsharedsets_*` |
| `bidmodifiers_toggle` | `direct bidmodifiers toggle` removed in CLI 0.2.8; Yandex deprecated this API operation on 2025-11-13 |

## Testing Model

Three test modes:
1. **Cassettes** (default `pytest`) — recorded CLI responses in `tests/recordings/`, no network needed
2. **Mocks** (`pytest -m mocks`) — `unittest.mock.patch("subprocess.run")` for unreproducible edge cases
3. **Integration** (`pytest -m integration`) — live API, requires OAuth token

Cassette lifecycle: record → sanitize (strip secrets/commercial data) → commit → replay in tests. Audit script blocks commits containing leaked tokens or PII.

New tools added in v2 (`advideos_*`, `bids_set_auto`, `keywordbids_set_auto`, `retargeting_update`, etc.) currently have mock-only tests. Cassette recording is a tracked follow-up.

## Domain Notes

- All money parameters (bids, budgets, CPC/CPA, ceilings) are in **micro-units**: 15 RUB = 15,000,000. CLI 0.2.10+ rejects values `0 < x < 100_000` with a "did you mean × 1_000_000?" hint.
- API batch limit: max 10 IDs per request
- Campaign IDs ~73-77M range belong to a second account (foreign_campaign error)
- OAuth tokens stored in `${CLAUDE_PLUGIN_DATA}/tokens.json` (gitignored)
- CLI binary: `direct` (installed via `pip install direct-cli`)
- Language: project docs in Russian, code identifiers in English

## Breaking Changes (v1 → v2 migration)

See `server/contract.py` → `RENAMED_TOOL_MIGRATION` for the full old→new name mapping.
Key renames:

| Old name | New name |
|---|---|
| `campaigns_list` | `campaigns_get` |
| `ads_list` | `ads_get` |
| `adgroups_list` | `adgroups_get` |
| `keyword_bids_*` | `keywordbids_*` |
| `agency_clients_*` | `agencyclients_*` |
| `audience_targets_*` | `audiencetargets_*` |
| `smart_ad_targets_*` | `smartadtargets_*` |
| `dynamic_ads_*` | `dynamicads_*` |
| `negative_keyword_shared_sets_*` | `negativekeywordsharedsets_*` |
| `changes_checkcamp` | `changes_check_campaigns` |
| `changes_checkdict` | `changes_check_dictionaries` |
| `keywords_has_volume` | `keywordsresearch_has_search_volume` |
| `keywords_deduplicate` | `keywordsresearch_deduplicate` |
| `negative_keywords_*` | removed (transport-blocked) |
| `dynamic_targets_*` | merged into `dynamicads_*` |
| `smart_targets_*` | merged into `smartadtargets_*` |

## Breaking Changes (CLI 0.2.10 alignment)

- **`bidmodifiers_set`**: signature changed to `(id: int, value: int, extra_json?)`.
  Removed `campaign_id` and `modifier_type` — those were the legacy "broken by design"
  form (CLI itself documents that the API rejects it with `required field Id is omitted`).
  Use the `Id` returned by `bidmodifiers_add` to update an existing modifier.
- **`keywords_update`**: removed `bid` / `context_bid` parameters — CLI's
  `keywords update` does not accept bid flags. Use `keyword_bids_set` for bid changes.
  New params: `keyword`, `user_param_1`, `user_param_2`.
- **Parameter types**: all single-id parameters (`id`, `campaign_id`, `ad_group_id`, `keyword_id`,
  `client_id`, `region_id`, `retargeting_condition_id`, etc.) and money parameters
  (`bid`, `context_bid`, `search_bid`, `network_bid`, `max_bid`, `bid_ceiling`, `budget`,
  `filter_average_cpc`, `average_cpc`, `average_cpa`) migrated from `str | None` to
  `int | None`. Comma-separated batch params (`*_ids`) keep `str` (CLI requires the
  `"1,2,3"` format).
- **`bidmodifiers_get`**: new optional `levels` parameter (`"campaign"` or `"ad_group"`).
- **`campaigns_add`**: new optional `filter_average_cpc: int` and `counter_id: int`
  parameters (CLI 0.2.10 Smart campaigns).
- **`bidmodifiers_toggle`**: tool removed (CLI 0.2.8 deprecated; API removed 2025-11-13).
- **New tools**: 5 `strategies_*` (get/add/update/archive/unarchive) and 6
  `dynamicfeedadtargets_*` (get/add/delete/suspend/resume/set_bids).
- **Validation**: plugin no longer pre-validates money values — CLI's `MICRO_RUBLES`
  type now owns the contract (rejects `0 < x < 100_000` with a "did you mean × 1_000_000" hint).
