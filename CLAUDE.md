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
- CLI binary: `direct` (installed via `pip install direct-cli`). Minimum required: `direct-cli>=0.4.0`.
- `reports_custom(goal_ids=...)` adds per-goal output columns: `Conversions_<goal_id>_<attribution>` and same for `CostPerConversion`. Default attribution code is `LSC`.
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

## Breaking Changes (CLI 0.2.10 / 0.3.8 alignment)

- **`bidmodifiers_set`**: signature changed to
  `(id: int, value: int, dry_run: bool = False)`.
  Removed `campaign_id`, `modifier_type`, and free-form JSON updates. The CLI
  now exposes only typed flags for this operation. Use the `Id` returned by
  `bidmodifiers_add` to update an existing modifier.
- **`keywords_update`**: removed `bid` / `context_bid` parameters — CLI's
  `keywords update` does not accept bid flags. Use `keywordbids_set` for bid changes.
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

## Breaking Changes (CLI 0.3.8 alignment)

CLI 0.3.8 enforces strict WSDL parity for mutating commands. The plugin tools
were updated accordingly:

- **`ads_update`**: signature changed. `type` (TEXT_AD | TEXT_IMAGE_AD |
  MOBILE_APP_AD) is now **required**. The `status` parameter was removed — use
  `ads_suspend / ads_resume / ads_archive / ads_unarchive` for status changes.
  New optional fields: `title`, `text`, `href`, `image_hash`, `tracking_url`,
  `action`, `age_label`. CLI rejects invalid field/type combinations.
- **`ads_add`**: new optional fields `image_hash`, `tracking_url`, `action`,
  `age_label` mirror CLI 0.3.8 typed flags. Field/type compatibility is
  enforced by the CLI (TEXT_IMAGE_AD rejects title/text; MOBILE_APP_AD rejects
  href). Fields still missing typed CLI flags (Title2, SitelinkSetId,
  AdExtensions, VCardId, TurboPageId, DisplayUrlPath, Mobile) cannot be passed
  from MCP yet — tracked upstream as `axisrow/direct-cli#202`.
- **`feeds_add`**: `business_type` is now **required** (one of RETAIL, HOTELS,
  REALTY, AUTOMOBILES, FLIGHTS, OTHER). Free-form JSON payloads were removed
  because CLI 0.3.8 dropped the `--json` flag from `feeds add`.
- **`feeds_update`**: free-form JSON payloads were removed for the same reason.
- **`keywords_add`** / **`keywords_update`**: free-form JSON payloads were
  removed because CLI 0.3.8 has no `--json` flag. Bulk keyword loading still
  requires one CLI call per keyword — tracked upstream as
  `axisrow/direct-cli#203`.
- **`campaigns_add`**: `bidding_strategy` (which went through `--json`) removed
  in favour of typed `search_strategy: str`, `network_strategy: str`,
  `settings: list[str]` (repeatable `OPTION=VALUE`). Goals / CPA configuration
  is not yet typed in CLI — tracked upstream as `axisrow/direct-cli#204`.
- **`campaigns_update`**: `notification` (which went through `--json`) removed.
  New optional fields `start_date` / `end_date` mirror CLI 0.3.8 typed flags.
- **`dry_run` everywhere**: all mutating tools (`ads_add`, `ads_update`,
  `keywords_add`, `keywords_update`, `campaigns_add`, `campaigns_update`,
  `feeds_add`, `feeds_update`) accept `dry_run: bool = False`. When True,
  the CLI prints the outgoing request payload without sending it — useful
  for diagnosing API warning 10165 ("parameter will not be applied").
- **New tools**: 4 `v4forecast_*` (create / list / get / delete) for V4 Live
  budget forecasts, plus `v4account_*`, `v4events_get_events_log`, and
  `v4wordstat_*` wrappers for direct-cli typed v4 Live commands. Standalone
  `v4finance_*` tools remain blocked by manual-review/master-token policy.

## Breaking Changes (CLI 0.3.9 alignment)

CLI 0.3.9 added typed flags for the three mutating commands previously
flagged as gaps in the 0.3.8 section. All three upstream issues
(`axisrow/direct-cli#202`, `#203`, `#204`) are now closed. The plugin
exposes these flags without any breaking change to existing callers —
all new parameters are optional.

- **`ads_add`** / **`ads_update`**: 7 new optional fields covering the
  rest of `TextAdAddItem` / `TextAdUpdateItem`: `title2`,
  `display_url_path`, `mobile` (YES / NO), `vcard_id`,
  `sitelink_set_id`, `turbo_page_id`, `ad_extensions` (comma-separated
  IDs). The plugin validates `mobile ∈ {YES, NO}` before invoking the
  CLI; every other field/type compatibility check stays on the CLI side.
  `image_hash` is now valid for `TEXT_AD` (was previously documented as
  TEXT_IMAGE_AD / MOBILE_APP_AD only).
- **`keywords_add`**: batch mode through `from_file` (path to a JSONL
  file) or `keywords_json` (inline JSON array). Mutex with the single
  `keyword` form — passing zero or more than one of the three returns
  `ToolError(error="missing_mode" | "conflicting_modes")` without
  invoking the CLI. Per-row WSDL CamelCase keys: required `Keyword` and
  `AdGroupId` unless top-level `ad_group_id` provides the default; optional
  `Bid`, `ContextBid`, `UserParam1`, and `UserParam2`. Per-row `AdGroupId`
  overrides the default. `Bid`/`ContextBid` are documented `Keywords.add`
  fields, but they are strategy-dependent: do not set them for auto-strategy /
  RSYA (РСЯ) JSONL or inline JSON imports because Yandex ignores them and
  returns warning `10160`.
  CLI 0.3.9 forwards the array as a single Yandex Direct
  API request (up to 1000 keywords per call). The plugin does not read
  `from_file` itself — CLI opens the path.
- **`campaigns_add`**: 8 new optional fields for CPA strategies and
  cross-cutting `CampaignAddItem` configuration: `counter_ids`
  (csv for TextCampaign / DynamicText), `goal_id`, `priority_goals`
  (csv `goal_id:value`), `average_cpa`, `crr`, `bid_ceiling`,
  `notification_json`, `time_targeting_json`. Strategy-subtype
  compatibility (`--crr` only on `PAY_FOR_CONVERSION_CRR`,
  `--priority-goals` only on `*_MULTIPLE_GOALS`, `--counter-ids` not for
  Smart, etc.) is enforced by CLI `UsageError` and propagates through
  `handle_cli_errors` — the plugin does not duplicate cross-field
  validation.

Closes plugin issues `#110`, `#111`, `#112`.

## Breaking Changes (CLI 0.3.11 alignment)

- **`direct-cli>=0.3.11` required**: the minimum CLI version was raised
  from 0.3.10. Installs running CLI 0.3.10 will be rejected by the
  version probe in `server/cli/runner.py` (the runtime floor moved to
  `MIN_DIRECT_VERSION = (0, 3, 11)`).

- **`v4account_account_management` renamed to `v4account_update_account`**:
  the old name is mapped in `RENAMED_TOOL_MIGRATION`. Existing callers
  using keyword arguments (`account_id=...`, `day_budget=...`) can switch
  the tool name with no other change; the signature is identical.

- **New tools** completing the v4 Live AccountManagement surface, now that
  CLI 0.3.11 ships typed flags for every action:

  - `v4account_get_accounts(logins?, account_ids?)` — read, no
    `dry_run`/`sandbox` required. Any combination of selectors is
    accepted (both at once map to one ``SelectionCriteria`` on the v4
    Live side); omit both to list every shared account the caller owns
    (``--action Get`` без ``SelectionCriteria``). Adds the AccountIDs
    selector that `balance_get` does not expose.
  - `v4account_deposit(payment, currency, origin?, contract?, operation_num?)`
  - `v4account_invoice(payment, currency, operation_num?)`
  - `v4account_transfer_money(from_account_id, to_account_id, amount, currency, operation_num?)`

  All three financial tools require `dry_run=True` or `sandbox=True`.
  **Finance, master, and finance-login tokens are NOT accepted as MCP
  parameters** — set them in environment variables instead:
  `YANDEX_DIRECT_FINANCE_TOKEN`, `YANDEX_DIRECT_MASTER_TOKEN`,
  `YANDEX_DIRECT_FINANCE_LOGIN`. `direct-cli` 0.3.11 reads them from
  env transparently. This keeps secrets out of MCP argv, logs, and
  Claude context (closes the high-severity adversarial-review finding
  from PR #119). The `operation_num` (idempotency token) may be passed
  as a parameter — it is not a secret.

- **`balance_get` unchanged**: still wraps `direct balance` (Logins-only).
  For the AccountIDs selector use `v4account_get_accounts`.

Closes plugin issue `#120`.

## Breaking Changes (CLI 0.3.13 alignment)

- **`direct-cli>=0.3.13` required**: the minimum CLI version was raised
  from 0.3.11. `MIN_DIRECT_VERSION` in `server/cli/runner.py` moved to
  `(0, 3, 13)`. Installs running CLI 0.3.12 or below will be rejected by
  the version probe.

- **CLI money-unit contract restored**: CLI 0.3.13 reverted the brief
  decimal-rubles experiment and reunified every campaigns money flag on
  `MICRO_RUBLES` (`axisrow/direct-cli#399`). The plugin can therefore
  forward all 147 new bidding-strategy detail flags as plain `int`
  micro-units without compensating for split unit types.

- **`campaigns_add` and `campaigns_update`**: 147 new optional
  bidding-strategy detail parameters covering every campaign type ×
  Search/Network in WSDL-parity form:

  - TextCampaign Search PlacementTypes (3): `search_placement_*`.
  - CpmBannerCampaign strategy (6): `average_cpm`, `average_cpv`,
    `strategy_spend_limit` (micro-units), `strategy_start_date`,
    `strategy_end_date`, `strategy_auto_continue` (YES/NO).
  - TextCampaign Search/Network (13 + 14): `text_search_*`,
    `text_network_*`.
  - DynamicTextCampaign Search/Network (17 + 18): `dyn_search_*`,
    `dyn_network_*`.
  - SmartCampaign Search/Network (18 + 19): `smart_search_*`,
    `smart_network_*` (with per-campaign and per-filter variants —
    `*_filter_average_cpa` / `*_filter_average_cpc` map to the
    per-filter strategy subtype, everything else is per-campaign).
  - UnifiedCampaign Search/Network (11 + 9): `unified_search_*`,
    `unified_network_*`.
  - MobileAppCampaign Search/Network (9 + 10): `mobile_search_*`,
    `mobile_network_*`.

  Money parameters end in `*_spend_limit`, `*_cpc`, `*_cpa`, `*_cpi`,
  `*_pay_cpa`, `*_bid_ceiling`, `*_exploration_budget`,
  `*_exploration_min`, `*_exploration_min_budget`, `*_profitability`,
  `*_roi_coef`, `*_filter_average_cpa`, `*_filter_average_cpc` — all in
  **micro-units** (`int`), matching the `--budget` / `--average-cpa`
  contract. The agent converts user-supplied rubles before calling the
  tool; users are not expected to multiply by 1_000_000.

- **`campaigns_update` only**: 10 new `*_budget_type` parameters
  (`text_search_budget_type`, `text_network_budget_type`,
  `dyn_search_budget_type`, `dyn_network_budget_type`,
  `smart_search_budget_type`, `smart_network_budget_type`,
  `unified_search_budget_type`, `unified_network_budget_type`,
  `mobile_search_budget_type`, `mobile_network_budget_type`) switch a
  running strategy between `WEEKLY_BUDGET` and `CUSTOM_PERIOD_BUDGET`
  without re-sending the rest of the strategy. CLI exposes these only on
  `campaigns update`; `campaigns_add` rejects them by signature.

- **All new parameters are optional**: no breaking change for existing
  callers. Strategy-subtype compatibility (e.g. `*_filter_average_cpa`
  only on the `*_PER_FILTER` Smart subtype, `*_weekly_spend_limit`
  mutually exclusive with `*_custom_period_spend_limit`,
  `*_clicks_per_week` only on `WEEKLY_CLICK_PACKAGE`) is enforced by CLI
  `UsageError` and propagates through `handle_cli_errors` — the plugin
  does not duplicate cross-field validation.

Closes plugin issue tracking the 0.3.13 bump.

## Breaking Changes (CLI 0.3.14 alignment)

- **`direct-cli>=0.3.14` required**: the minimum CLI version was raised
  from 0.3.13. `MIN_DIRECT_VERSION` in `server/cli/runner.py` moved to
  `(0, 3, 14)`. Installs running CLI 0.3.13 or below will be rejected by
  the version probe.

- **No `campaigns_add` / `campaigns_update` signature changes**: CLI
  0.3.14 ships ~210 typed flags (200 shared add+update + 10 update-only
  `*-budget-type` switches) on `campaigns add` / `campaigns update`,
  all of which were already proxied through `CAMPAIGN_MUTATION_OPTIONS`
  and `CAMPAIGN_UPDATE_ONLY_OPTIONS` in the 0.3.13 alignment. The
  micro-units contract is preserved (`MICRO_RUBLES` everywhere).

- **New `v4finance` CLI group**: CLI 0.3.14 exposes typed `v4finance`
  subcommands for the v4 Live Financial API — `get-clients-units`,
  `get-credit-limits`, `check-payment`, `create-invoice`,
  `transfer-money`, `pay-campaigns`. These are **intentionally not
  surfaced as MCP tools** and remain catalogued in
  `server/contract.py` → `V4_LIVE_BLOCKED_METHODS` with
  `_FINANCIAL_REASON`. Financial operations require manual review and
  master-token issuance through the Direct UI; exposing them via MCP
  would put high-value mutating endpoints behind an LLM tool call.

  Unlike `v4account_deposit` / `v4account_invoice` /
  `v4account_transfer_money` (which operate on shared-accounts and
  enforce `dry_run=True` or `sandbox=True`), the new v4finance group
  has no shared-account / dry-run safety net at the API level — every
  call is a real money movement against a live campaign or client
  balance. That is why the v4account family is exposed (with env-only
  finance tokens) but v4finance is not.

  The blocked list already covered all six methods before the bump
  (CLI added the typed subcommands in 0.3.14, but the v4 methods
  themselves existed earlier), so no contract changes were needed.
  `PayCampaignsByCard` is still listed with `_NO_CLI_REASON` — CLI
  0.3.14 does not type that subcommand.

Closes plugin issue tracking the 0.3.14 bump.

## Breaking Changes (CLI 0.3.15 alignment)

- **`direct-cli>=0.3.15` required**: the minimum CLI version was raised
  from 0.3.14. `MIN_DIRECT_VERSION` in `server/cli/runner.py` moved to
  `(0, 3, 15)`. Installs running CLI 0.3.14 or below will be rejected by
  the version probe.

- **No plugin signature changes**: every CLI 0.3.15 breaking change is
  confined to the `v4finance` group, which the plugin intentionally does
  **not** surface as MCP tools (all six v4finance methods stay catalogued
  in `server/contract.py` → `V4_LIVE_BLOCKED_METHODS` with
  `_FINANCIAL_REASON` / `_NO_CLI_REASON`). The removed CLI flags were
  never proxied through MCP, so no tool signatures or contract entries
  changed. The micro-units / `MICRO_RUBLES` contract is preserved.

  CLI 0.3.15 brings the v4finance wire-bodies to 1:1 parity with the
  official v4 docs:

  - `v4finance transfer-money` / `create-invoice` / `pay-campaigns` no
    longer accept `--currency`; the `PayCampElement` wire-body carries
    only `CampaignID` and `Sum` (conventional units), matching
    `dg-v4/reference/{TransferMoney,CreateInvoice,PayCampaigns}`.
  - `v4finance pay-campaigns` no longer accepts `--pay-method Overdraft`;
    only `Bank` remains (the documented value).

  These remain inaccessible from MCP for the same reason given in the
  0.3.14 section: v4finance calls are real money movements against live
  campaign/client balances with no shared-account / dry-run safety net,
  so they require manual review and master-token issuance through the
  Direct UI rather than an LLM tool call.

Closes plugin issue tracking the 0.3.15 bump.

## Breaking Changes (CLI 0.3.16 alignment)

- **`direct-cli>=0.3.16` documented**: CLI 0.3.16 was the alignment
  target. Historical note: this doc bump only updated `CLAUDE.md` — the
  runtime floor (`MIN_DIRECT_VERSION` in `server/cli/runner.py`,
  `pyproject.toml`, `README.md`) was *not* moved and stayed at
  `(0, 3, 15)` / `>=0.3.15`. The intended `(0, 3, 16)` / `>=0.3.16`
  bump never landed in code; the runtime floor was next raised directly
  to `(0, 4, 0)` / `>=0.4.0` in the CLI 0.4.0 alignment below, which
  resynced all four locations. Because 0.3.16 was a v4finance-only
  regression fix with no MCP-surface impact, the stale runtime floor had
  no functional effect.

- **No plugin signature changes**: CLI 0.3.16 is a regression-fix that
  reverts the 0.3.15 wire-shape changes (PRs #441/#442/#443), confined
  entirely to the `v4finance` group, which the plugin intentionally does
  **not** surface as MCP tools (all six v4finance methods stay catalogued
  in `server/contract.py` → `V4_LIVE_BLOCKED_METHODS` with
  `_FINANCIAL_REASON` / `_NO_CLI_REASON`). The restored CLI flags were
  never proxied through MCP, so no tool signatures or contract entries
  changed. The micro-units / `MICRO_RUBLES` contract is preserved.

  CLI 0.3.16 realigns the v4finance wire-bodies with the **Live 4** docs
  (`dg-v4/live/*`) rather than the legacy reference docs
  (`dg-v4/reference/*`) that 0.3.15 mistakenly targeted:

  - `v4finance transfer-money` / `create-invoice` / `pay-campaigns`
    require `--currency` again and re-emit `Currency` on every
    `PayCampElement` / `Payments[]` item — `dg-v4/live/*` marks
    `Currency` obligatory.
  - `v4finance pay-campaigns` accepts `--pay-method Overdraft` again
    (Live 4 adds it for direct advertisers, paired with `Bank` for
    agencies; only `Bank` keeps the `--contract-id` requirement).

  These remain inaccessible from MCP for the same reason given in the
  0.3.14/0.3.15 sections: v4finance calls are real money movements
  against live campaign/client balances with no shared-account /
  dry-run safety net, so they require manual review and master-token
  issuance through the Direct UI rather than an LLM tool call.

Closes plugin issue tracking the 0.3.16 bump.

## Breaking Changes (CLI 0.4.0 alignment)

- **`direct-cli>=0.4.0` required**: the minimum CLI version was raised
  from 0.3.15 to 0.4.0. `MIN_DIRECT_VERSION` in `server/cli/runner.py`
  moved to `(0, 4, 0)`. This also unifies the runtime floor with the
  documented one — the 0.3.16 doc bump left `MIN_DIRECT_VERSION`,
  `pyproject.toml`, and `README.md` at `0.3.15` (only `CLAUDE.md`
  advanced), so this release resyncs all four. Installs running CLI
  0.3.x or below will be rejected by the version probe.

- **No plugin signature changes**: CLI 0.4.0 is a large release —
  rewritten auth, ~hundreds of typed bidding-strategy / ad-type flags,
  and a new `--locale` switch — but every change either was already
  proxied ahead of time in the 0.3.x alignments or does not touch the
  MCP surface:

  - **Auth contract already implemented.** CLI 0.4.0 makes
    `direct auth login` canonical (`--profile`, `--oauth-token`,
    `--code -` / `--code-stdin`, OAuth refresh tokens), removes
    `direct auth setup`, and makes the deprecated `direct-cli`
    entrypoint exit with an error. `server/tools/auth_tools.py` already
    drives `direct auth login --profile … --oauth-token …` and
    `--code -` / `--code-stdin` — it never called `auth setup`. The
    `~/.direct-cli/auth.json` shape the plugin reads (`profiles`,
    `active_profile`, per-profile `token` / `login` / `expires_at` /
    `refresh_token` / `source`) matches CLI 0.4.0 exactly. The MCP
    tools `auth_status` / `auth_setup` / `auth_login` are unchanged.

  - **All typed flags already proxied.** Every CLI 0.4.0 typed flag for
    the mutating commands (`ads add/update`, `adgroups add/update`,
    `campaigns add/update` — all 218 add/update flags build from the
    plugin — `bidmodifiers add`, `bids`, `keywordbids`, `keywords`,
    `vcards`, `clients` ERIR, `agencyclients`, `strategies`,
    `retargeting`, `sitelinks`, `adimages`, `advideos`) was already
    wired through MCP in the 0.3.9–0.3.16 alignments. No tool signature
    needed to change.

  - **New global `--locale ru|en`** (env `YANDEX_DIRECT_CLI_LOCALE`)
    switches CLI help/message language. It is read-only ergonomics; the
    plugin uses the CLI default and does not forward it, so it does not
    affect any tool.

  - **`v4finance` stays blocked.** CLI 0.4.0 keeps the six v4finance
    subcommands (`get-clients-units`, `check-payment`, `create-invoice`,
    `transfer-money`, `pay-campaigns`, `get-credit-limits`); they remain
    catalogued in `server/contract.py` → `V4_LIVE_BLOCKED_METHODS` with
    `_FINANCIAL_REASON` / `_NO_CLI_REASON` and are intentionally not
    surfaced as MCP tools (real money movements with no shared-account /
    dry-run safety net; master-token issuance through the Direct UI).

  - **All CLI 0.4.0 groups/subcommands are covered** by existing tools;
    no new API service appeared that would require a new tool.
    `v4goals` / `v4tags` were already added in earlier releases.

Closes plugin issue tracking the 0.4.0 bump.

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
