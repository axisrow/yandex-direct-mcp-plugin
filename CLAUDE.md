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

Tool-surface selection (`server/config.py`, default = full 146 tools):

- `YANDEX_DIRECT_TOOL_PROFILE` — `full` | `core` | `analytics` | `campaign-editor`
- `YANDEX_DIRECT_ENABLED_GROUPS` / `YANDEX_DIRECT_DISABLED_GROUPS` — group allow/deny (service; action `read`/`mutate`/`destructive` (delete only)/`lifecycle` (suspend/resume/archive/unarchive/moderate); product-area names; or the `financial` risk group for money-movement v4account tools)
- `YANDEX_DIRECT_ENABLED_TOOLS` / `YANDEX_DIRECT_DISABLED_TOOLS` — per-tool overrides

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
│   ├── direct-ads/SKILL.md      # Ad copywriting skill
│   └── direct-eda/SKILL.md      # Exploratory analysis over reports skill
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

## MCP Tools (146 total) + 1 Prompt

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
| `adgroups_add` | Create ad group (single, or batch via `from_file`/`adgroups_json`) |
| `adgroups_update` | Update ad group (single by id, or batch via `from_file`/`adgroups_json`) |
| `adgroups_delete` | Delete ad groups |
| `ads_get` | List ads by campaign IDs |
| `ads_add` | Create ad (single, or batch via `from_file`/`ads_json`) |
| `ads_update` | Update ad (single by id, or batch via `from_file`/`ads_json`); `clear_image_hash` resets AdImageHash |
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

### Plugin tools (4)

Auth/utility tools unrelated to Direct API parity.

| Tool | Purpose |
|---|---|
| `auth_status` | Check direct auth profile status |
| `auth_setup` | Submit authorization code or direct token |
| `auth_login` | Interactive OAuth flow with elicitation |
| `tool_help` | Return the full docstring (parameters, examples, constraints) for any tool on demand. Every tool exposes only a one-line description to keep startup context small; call `tool_help('<name>')` before using an unfamiliar tool. Omit the name to list all tools. |

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
- CLI binary: `direct` (installed via `pip install direct-cli`). Minimum required: `direct-cli>=0.4.3`.
- `reports_custom(goal_ids=...)` adds per-goal output columns: `Conversions_<goal_id>_<attribution>` and same for `CostPerConversion`. Default attribution code is `LSC`.
- Language: project docs in Russian, code identifiers in English

## Breaking Changes (0.3.0 — progressive disclosure of tool descriptions)

- **Tools now expose a one-line `description`; full docs moved to `tool_help`.**
  Previously every tool's entire docstring (parameter reference, examples,
  constraints) was sent to the model as the tool `description` on every request
  — ~16.6k tokens of the plugin's tool-spec budget. Now each `@mcp.tool(...)`
  carries a short English `description=` (what it does + when to pick it over a
  sibling), and the full docstring is served on demand by a new meta-tool
  `tool_help('<name>')`. The function docstrings themselves are unchanged — they
  are simply no longer broadcast at startup.

- **Measured effect** (`python -m tests.measure_tool_tokens`, tiktoken
  cl100k_base): tool-spec budget **54,457 → 40,792 tokens (−25%)**; the
  descriptions portion **16,582 → 4,522 (−73%)**. JSON-Schema of parameters is
  untouched (that is a separate, riskier task — see issue #154 / Epic #149).

- **No API break.** Tool names, parameters and behavior are identical. The only
  surface change is what the model sees: short summaries instead of full docs.
  A client that relied on reading the long `description` text must now call
  `tool_help`.

- **Tool count 145 → 146.** One new plugin tool `tool_help`. Registered in
  `server/contract.py` (`PLUGIN_TOOL_NAMES`), `server/main.py`, the bundled
  `plugins/yandex-direct/server/main.py`, `CLAUDE.md`, and `README.md`.

## Breaking Changes (CLI 0.4.1 alignment)

- **Auth status delegated to `direct`**: the plugin no longer
  reads `~/.direct-cli/auth.json` directly. `auth_status()` delegates to
  `direct auth status --format json`, so effective env/.env/profile
  precedence stays owned by `direct-cli`.

- **`direct-cli>=0.4.1` alignment**: the minimum CLI bump
  exposed additional v4 Live commands and resynced `pyproject.toml`,
  `README.md`, and `hooks/setup.sh`. The current runtime floor is 0.4.1.

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

## Breaking Changes (CLI 0.4.2 alignment)

- **`direct-cli>=0.4.2` alignment**: the minimum CLI bump reflects
  the flag-rename breaking change below and resyncs `pyproject.toml`,
  `README.md`, `hooks/setup.sh`, and `server/cli/runner.py`.
  The current runtime floor is 0.4.2.

- **Nested FieldNames flags renamed**: CLI 0.4.2 renamed all
  sub-object FieldNames flags from `--*-fields` to `--*-field-names`
  (e.g. `--text-campaign-fields` → `--text-campaign-field-names`).
  The top-level `--fields` flag is unchanged. The MCP plugin's
  `CAMPAIGN_GET_SELECTOR_FLAGS` and `ads_get` now emit the new flag
  names. Python parameter names (`text_campaign_fields`, etc.) stay
  unchanged.

- **Empty SelectionCriteria guard**: CLI 0.4.2 rejects empty filter
  sets for 8 get-commands (`adgroups`, `ads`, `keywords`, `strategies`,
  `creatives`, `dynamicads`, `smartadtargets`, `audiencetargets`) with
  a clear `UsageError` instead of letting the request reach the API and
  fail with error 4001. No MCP plugin changes needed — the plugin
  already requires at least one filter for the affected tools.

- **Auth credential precedence reversed**: base environment variables
  (`YANDEX_DIRECT_TOKEN`, `YANDEX_DIRECT_LOGIN`) now override the
  active OAuth profile, reversing the previous order. No MCP plugin
  changes needed — auth precedence is owned by `direct-cli`.

- **No tool count change.** The 146-tool surface is unchanged.

## Feature Changes (CLI batch-mode + clear-image-hash sync)

Surfaces direct-cli `main` features (#552, #562–565) that the plugin did not
yet forward. **Additive only** — existing single-item calls are unchanged.

- **Batch mode for `ads_add` / `ads_update` / `adgroups_add` /
  `adgroups_update`.** Each now accepts `from_file` (path to a JSONL file) and
  `ads_json` / `adgroups_json` (inline JSON array) in addition to single-item
  flags. Modes are mutually exclusive; rows use the CLI's kebab-key flag form
  (`adgroup-id`, `image-hash`, `clear-image-hash`, ...). The CLI chunks the
  batch (100/chunk, API ceiling 1000) and reports partial success — the plugin
  forwards the result. Single-item required params became optional in the
  signature so batch mode can omit them; a `missing_mode` / `conflicting_modes`
  guard mirrors `keywords_add`.

- **`ads_update(clear_image_hash=True)`** emits `--clear-image-hash`, resetting
  `AdImageHash` to null (TEXT_AD / DYNAMIC_TEXT_AD / MOBILE_APP_AD). Mutually
  exclusive with `image_hash` (`conflicting_image_hash`). The CLI rejects it for
  image-ad subtypes (error 8000) — the plugin does not duplicate that guard.
  Closes the long-standing "cannot reset AdImageHash" gap (issue #181/#171-B).

- **`ads_update` now needs `type` in single mode.** direct-cli `main` requires
  `--type` to pick the typed payload branch; the plugin forwards the CLI's
  error rather than re-validating.

- **Released in direct-cli 0.4.3 (PyPI).** These features previously lived only
  on direct-cli `main`; 0.4.3 ships them on PyPI (#562–565 batch ads/adgroups,
  #552 `--clear-image-hash`). No git/dev build is needed any more — see the
  CLI 0.4.3 alignment section below; the runtime floor is now `direct-cli>=0.4.3`.

- **No tool count change.** 146 tools — new parameters, not new tools.

- **Resolved in direct-cli 0.4.3 (#571/#577):** SelectionCriteria array-length
  limits on the remaining `get` commands (the wrong `check_batch_limit(max=10)`,
  plugin issue #201) are now enforced by direct-cli for all 8 commands the
  plugin previously guarded duplicate-style (`ads`, `adgroups`, `bids`,
  `bidmodifiers`, `audiencetargets`, `dynamicfeedadtargets`, `campaigns`,
  `keywords`). The plugin drops its guards in a separate section below.

## Breaking Changes (CLI 0.4.3 alignment)

- **`direct-cli>=0.4.3` alignment**: the minimum CLI bump promotes to PyPI the
  features the plugin already forwards from direct-cli `main`. The runtime floor
  moves to 0.4.3 in the 4 canonical places (`pyproject.toml`, `hooks/setup.sh`
  ×2, `README.md`); the `_has_direct_cli_0402` venv guard became
  `_has_direct_cli_0403` (`< (0, 4, 3)`).

- **No MCP surface change.** 0.4.3 is a stabilization release — it bundles the
  features the plugin was already built against on `main` and adds nothing the
  plugin does not yet forward:

  - **Batch `ads add`/`update` + `adgroups add`/`update`** (#562–565) — already
    forwarded via `from_file` / `ads_json` / `adgroups_json` (see the batch-mode
    feature section above). The CLI now uses a shared `_batch.py` engine and
    `build_ad_object()` / `build_adgroup_object()` extraction; the wire form the
    plugin emits is unchanged.
  - **`ads update --clear-image-hash`** (#552) — already forwarded as
    `ads_update(clear_image_hash=True)`.
  - **IntRange(min=1) on every mutation selector** (#558) — CLI-owned
    pre-validation; the plugin proxies the `UsageError`, no duplicate guard.
  - **SelectionCriteria preflight on `keywordbids/dynamicads/smartadtargets
    get`** (#555) — CLI-owned; this is exactly the validation the plugin is
    delegating per issue #201 / direct-cli #571.
  - **Error 8300 hint on delete/moderate** (#548) — the CLI now appends its own
    8300 hint; the plugin keeps its structured `error`/`hint` mapping on top
    (value-add, not a duplicate — same rationale as #184/#185).
  - **`adgroups` empty-string CSV-ID rejection** (#570) — CLI-owned, the dup
    the plugin closed as superseded (plugin #174).

- **Tool count unchanged (146).** Updated `pyproject.toml`, `hooks/setup.sh`,
  `README.md`, and this file; plugin/marketplace version bumped via
  `scripts/update-version.sh`.

## Breaking Changes (#220-A — ads param grouping for token budget)

- **`ads_add` / `ads_update` extension families are now nested dict params.**
  Following the #154 strategy-dict pattern, flat families collapse into single
  `dict | None` params to shrink the JSON Schema FastMCP broadcasts (part of
  #149). Dict keys are the **old flat param names**, and
  `helpers.expand_grouped_dicts` unfolds them before `append_cli_options`, so the
  generated `direct` argv is **byte-for-byte identical**.

  - `price_extension_options` ← `price_extension_{price,old_price,price_qualifier,price_currency}`
  - `video_extension_options` ← `video_extension_{creative_id,ids}`
  - `callouts_options` ← `callouts_{add,remove,set}` (`ads_update` only)
  - `creative_options` ← `creative_id`, `creative_erir_ad_description` (`ads_update`; in `ads_add`, `creative_id` stays flat)
  - `text_source_options` ← `title_sources`, `text_sources`, `default_texts`

- **Effect** (`measure_tool_tokens`, approx): `ads_update` 46→37 params (≈1262→1042),
  `ads_add` 41→35 (≈1118→963); total tool-spec 34,781→34,406. `TOTAL_TOKEN_CEILING`
  lowered 38,000→35,500.

- **New shared helper** `server/tools/helpers.py:expand_grouped_dicts(values, registry)`
  (reused by campaigns in #220-B). Parity guard treats absorbed flat names as
  exposed via `_ads_extra_dict_param_names()`.

- **No CLI/API break.** Only the tool's parameter shape changed. A caller that
  passed the old flat params must move them under the matching `*_options` dict.

## Breaking Changes (#220-B — campaigns flat-family grouping)

- **`campaigns_add` / `campaigns_update` remaining flat families are now dict
  params** (same technique as #154 strategy dicts and #220-A ads dicts; argv
  byte-identical via `helpers.expand_grouped_dicts`):

  - `notification_options` ← `notification_{email,check_position_interval,warning_balance,send_account_news,send_warnings}`
  - `time_targeting_options` ← `time_targeting_schedule`, `consider_working_weekends`, `holidays_{suspend_on_holidays,bid_percent,start_hour,end_hour}`
  - `frequency_cap_options` ← `frequency_cap_{impressions,period_days,period_all}`
  - `relevant_keywords_options` ← `relevant_keywords_{budget_percent,mode,optimize_goal_id}`
  - `package_platform_options` ← `package_platform_*` (7)
  - `sms_options` ← `sms_{events,time_from,time_to}`
  - `search_placement_options` ← `search_placement_*` (3)
  - `cpm_strategy_options` ← `strategy_{auto_continue,end_date,spend_limit,start_date}`

  Small families (`attribution_model`, `package_strategy_*`, `dynamic_placement_*`)
  stay flat. `repeat`/`is_flag` member behavior (`time_targeting_schedule`,
  `frequency_cap_period_all`) is preserved.

- **Effect** (`measure_tool_tokens`, approx): `campaigns_update` 77→51 params
  (2337→1567), `campaigns_add` 76→50 (2313→1543); total tool-spec 34,406→32,866.
  `TOTAL_TOKEN_CEILING` lowered 35,500→33,500. Combined #220 saving ≈ 1,915 tokens.

- **No CLI/API break.** Parameter shape only; move old flat params under the
  matching `*_options` dict.

## Breaking Changes (#201 — drop check_batch_limit guards on read-get tools)

- **`check_batch_limit(max=10)` removed from 8 read-get tools.** The plugin's
  blanket 10-cap was wrong for most SelectionCriteria filters — too permissive
  on 1000-cap fields (e.g. `bids get` `AdGroupIds`), too strict on filters that
  are uncapped (e.g. `ads get` `Ids`) or capped at 2 (e.g. `dynamicfeedadtargets
  get` `CampaignIds`). direct-cli 0.4.3 (#571/#577) now enforces the real,
  live-measured per-method/per-filter limits via `enforce_criteria_array_limits`
  — the plugin no longer duplicates that validation.

  Affected tools: `ads_get`, `adgroups_get`, `bids_get`, `bidmodifiers_get`,
  `audiencetargets_get`, `dynamicfeedadtargets_get`, `campaigns_get`,
  `keywords_get`. Each tool's docstring now states the real per-filter limits
  in one line (e.g. `Limits: CampaignIds≤10, AdGroupIds≤1000; KeywordIds
  unlimited.`) so the LLM picks valid inputs; the CLI is the source of truth
  and enforces them at the boundary, per [[cli-plugin-responsibility]].

- **`MIN_DIRECT_VERSION` bumped to (0, 4, 3)** in `server/cli/runner.py` to
  match `pyproject.toml` / `hooks/setup.sh` / `README.md` (the runtime probe
  was lagging at (0, 4, 2)). Without the bump, a fresh install on a
  pre-0.4.3 venv would silently pass the package resolver and then skip the
  CLI's preflight, regressing to opaque API error 4001 instead of a typed
  `UsageError`.

- **Out of scope (kept as-is):** the four small read-get tools whose `Ids`
  array #571 measured as uncapped — `strategies_get`, `sitelinks_get`,
  `vcards_get`, `adextensions_get` — still carry the plugin's `check_batch_limit`
  guard for defense-in-depth. `v4tags` (real 2000 / 30 / 10 limits) and
  `changes_check` (dynamic `limit`) keep their typed guards; `run_single_id_batch`
  is fan-out protection, not an API limit, and stays.

- **No tool count change (146).** Closes #201.
