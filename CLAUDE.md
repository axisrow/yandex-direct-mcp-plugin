# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Code plugin for managing Yandex.Direct advertising campaigns. Wraps `direct` CLI (Python) via an MCP server and delegates authentication to direct auth profiles.

**Status:** Implemented.

## Architecture

```
direct (Python CLI)         — talks to Yandex.Direct API
       ↑
server/main.py (MCP)        — FastMCP server (stdio transport)
       ↑
server/contract.py          — machine-readable parity layer (129 tools)
server/cli/runner.py        — subprocess wrapper over `direct`
server/tools/               — 129 MCP tools across 34 active modules
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

- MCP **never** calls Yandex.Direct directly. This is absolute — even as a workaround for a missing/broken CLI feature, the plugin does not bypass `direct-cli` via `urllib`, raw HTTP, or `tapi-yandex-direct` imports. If CLI lacks something, file an upstream issue in `axisrow/direct-cli` and wait for the release.
- `direct` is the only execution/transport boundary.
- `tapi-yandex-direct` naming is the default source reused by the CLI.
- WSDL / Reports spec wins when CLI convenience names drift.

The machine-readable parity source is `server/contract.py`
(`PUBLIC_CONTRACT`, `TRANSPORT_BLOCKED_OPERATIONS`, `RENAMED_TOOL_MIGRATION`).

## Tech Stack

- **Python >= 3.11**, no Node.js
- **mcp** (PyPI) for MCP server, **direct-cli** for API transport and auth profiles
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

### 2. direct auth profile

Run `auth_login` (interactive, uses elicitation) or `auth_setup` (manual code/token entry). Token and login are saved by `direct` in `~/.direct-cli/auth.json`.

### Priority

`direct-cli` resolves explicit CLI/env credentials first, then the selected/active profile.

### Environment variables

- `YANDEX_DIRECT_TOKEN` — direct OAuth token
- `YANDEX_DIRECT_LOGIN` — Direct Client-Login
- `YANDEX_DIRECT_CLI_PATH` — explicit `direct` binary path

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
│       ├── reports.py           # reports_get/reports_custom/list_types
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

## MCP Tools (145 total) + 1 Prompt

The canonical source of truth for tool names is `server/contract.py`.
Naming follows `service_method` from `tapi-yandex-direct`/`direct-cli`;
WSDL/reports spec wins when there is drift.

### Direct API tools (128)

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
| `keywords_update` | Update keyword text or user params (use `keywordbids_set` for bids) |
| `keywords_add` | Add keywords |
| `keywords_delete` | Delete keywords |
| `keywords_suspend` | Suspend keywords |
| `keywords_resume` | Resume keywords |
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
| `changes_check` | Check changes since timestamp (filter by exactly one of campaign_ids/ad_group_ids/ad_ids; limits 3000/10000/50000) |
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
| `reports_custom` | Full Reports API surface: arbitrary FieldNames, filters, ordering, pagination, file output, processing-mode/language/attribution/skip-* CLI 0.3.10 flags; honors `response_format` (json/tsv/csv/table) both for in-memory and `output_path` |
| `v4account_get_accounts` | Read v4 Live shared accounts via AccountManagement Get (pass `logins` OR `account_ids`). |
| `v4account_update_account` | Update v4 Live shared-account settings via AccountManagement Update (dry_run or sandbox required). |
| `v4account_deposit` | Deposit funds via AccountManagement Deposit. Finance/master tokens MUST come from env (`YANDEX_DIRECT_FINANCE_TOKEN`, `YANDEX_DIRECT_MASTER_TOKEN`). |
| `v4account_invoice` | Issue invoice payments via AccountManagement Invoice. Same env-only token policy as deposit. |
| `v4account_transfer_money` | Transfer funds between shared accounts via AccountManagement TransferMoney. Same env-only token policy. |
| `v4account_enable_shared_account` | Enable v4 Live shared account in dry-run or sandbox |
| `v4events_get_events_log` | Get v4 Live events log entries |
| `v4forecast_create` | Create v4 Live budget forecast |
| `v4forecast_list` | List v4 Live budget forecasts |
| `v4forecast_get` | Get a ready v4 Live budget forecast |
| `v4forecast_delete` | Delete a v4 Live budget forecast |
| `v4wordstat_create_report` | Create v4 Live Wordstat report |
| `v4wordstat_list_reports` | List v4 Live Wordstat reports |
| `v4wordstat_get_report` | Get a ready v4 Live Wordstat report |
| `v4wordstat_delete_report` | Delete v4 Live Wordstat report |
| `v4keywords_get_suggestion` | Get related keyword suggestions (up to 20 phrases; spends API points) |
| `v4adimage_get` | Read ad-image associations (AdImageAssociation Get) |
| `v4adimage_set` | Link/unlink ad images (AdImageAssociation Set) |

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
| `auth_status` | Check direct auth profile status |
| `auth_setup` | Submit authorization code or direct token |
| `auth_login` | Interactive OAuth flow with elicitation |

| Prompt | Purpose |
|---|---|
| `oauth_login` | Start direct auth profile authorization flow |

### Transport-blocked operations

Operations in the WSDL/tapi surface that have no `direct` subcommand.
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
- OAuth tokens are stored as direct auth profiles, normally in `~/.direct-cli/auth.json`.
- CLI binary: `direct` (installed via `pip install direct-cli`). Minimum required: `direct-cli>=0.4.1`.
- `reports_custom(goal_ids=...)` adds per-goal output columns: `Conversions_<goal_id>_<attribution>` and same for `CostPerConversion`. Default attribution code is `LSC`.
- Language: project docs in Russian, code identifiers in English

## Breaking Changes (CLI 0.4.1 alignment)

- **`direct-cli>=0.4.1` required**: the minimum CLI version was raised
  from 0.4.0. `MIN_DIRECT_VERSION` in `server/cli/runner.py` moved to
  `(0, 4, 1)`, and `pyproject.toml`, `README.md`, and `hooks/setup.sh`
  were resynced. `hooks/setup.sh` had drifted (it still installed
  `direct-cli>=0.3.11` via `_has_direct_cli_0311`); the probe is now
  `_has_direct_cli_0401` / `>=0.4.1`, matching the runtime floor.

- **Three new v4 Live MCP tools.** CLI 0.4.1 ships typed subcommands for
  three v4 Live methods that were previously catalogued in
  `server/contract.py` → `V4_LIVE_BLOCKED_METHODS` with `_NO_CLI_REASON`
  ("direct-cli does not expose a typed subcommand"). Two are now exposed
  as MCP tools; the third stays blocked under the financial policy:

  - `v4keywords get-suggestion` → **`v4keywords_get_suggestion(keywords)`**
    (GetKeywordsSuggestion). Returns up to 20 related phrases; spends API
    points (error_code=152 when exhausted). New module
    `server/tools/v4keywords.py`.
  - `v4adimage get` / `v4adimage set` → **`v4adimage_get(...)`** /
    **`v4adimage_set(associations, dry_run=False)`** (AdImageAssociation
    Get/Set). `get` reads ad↔image links (empty filter ⇒ up to 10000);
    `set` links (`AD_ID=HASH`) or unlinks (`AD_ID`) up to 10000 per call.
    New module `server/tools/v4adimage.py`. The single AdImageAssociation
    method is split into two action-scoped tools, mirroring the CLI's two
    subcommands (same split pattern as `v4account_*` for AccountManagement).
  - `v4finance pay-campaigns-by-card` → **stays blocked**. CLI 0.4.1 types
    the subcommand, so its `V4_LIVE_BLOCKED_METHODS` entry switched from
    `_NO_CLI_REASON` to `_FINANCIAL_REASON` — like every other `v4finance`
    method it is a real money movement with no shared-account / dry-run
    safety net and is intentionally not surfaced via MCP.

  Method support was verified with live calls against the Yandex API
  (`v4keywords get-suggestion` returned suggestions; `v4adimage get`
  returned real associations; `v4adimage set --dry-run` built the correct
  request body); CLI sources carry a `Docs-verified 2026-05-28 against
  dg-v4/live/AdImageAssociation` marker.

- **Tool count 142 → 145** (Direct API 136 → 139). Updated in
  `server/contract.py`, `CLAUDE.md`, `README.md`, and `tests/test_server.py`.

- **Other CLI 0.4.1 changes do not touch the MCP surface**: stricter
  pre-call validation (`bids`/`keywordbids get`, `bids set-auto`,
  `reports get` empty-field rejection), error-handling consistency, an
  auth fix that resolves bare Client-Login via the v5 API, and a new
  Russian-default i18n layer with the `--locale` switch (the plugin uses
  the CLI default and does not forward it).

Closes plugin issue tracking the 0.4.1 bump.
