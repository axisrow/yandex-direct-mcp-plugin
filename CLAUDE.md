# CLAUDE.md

Claude Code plugin for managing Yandex.Direct advertising campaigns. Wraps the `direct` Python CLI via an MCP server (FastMCP, stdio); auth delegated to `direct` auth profiles. **Status:** Implemented.

## Architecture

```
MCP (server/main.py) → direct CLI → tapi-yandex-direct → Yandex.Direct API
```

- **MCP never calls Yandex.Direct directly** — always through `direct`, even to work around a missing/broken CLI feature. No `urllib`, raw HTTP, or `tapi-yandex-direct` imports. File upstream issues in `axisrow/direct-cli` and wait for the release.
- `direct` is the only execution/transport boundary. WSDL/Reports spec wins when CLI convenience names drift.
- Machine-readable parity source: `server/contract.py` (`PUBLIC_CONTRACT`, `TRANSPORT_BLOCKED_OPERATIONS`, `RENAMED_TOOL_MIGRATION`).
- `server/cli/runner.py` — `DirectCliRunner` subprocess wrapper. `server/tools/*.py` — 149 default tools across 42 modules, one module per service; the contract reserves 23 additional tools for opt-in bundles loaded by `server/optional_tools.py` as their implementation modules land. `server/tools/helpers.py` — shared validation (`parse_ids`, `check_batch_limit`).

## Commands

| Task | Command |
|------|---------|
| Install | `pip install -e ".[dev]"` (add `,docs` for Sphinx) |
| All tests (cassettes, no token) | `pytest` |
| Single test | `pytest tests/test_campaigns.py::test_campaigns_list -v` |
| Mock edge-case tests | `pytest -m mocks` |
| Integration tests (needs `.env` + a `direct` auth profile) | `pytest -m integration` |
| Record cassettes | `pytest --record` |
| Sanitize / audit cassettes | `python -m tests.sanitize` · `python -m tests.audit` |
| Lint / format | `ruff check .` · `ruff format .` |
| Type check | `mypy .` |
| Run server locally | `python3 server/main.py` |
| Build docs | `cd docs && make html` |

## Environment

- Python ≥ 3.11, no Node.js. Deps: `mcp`, `direct-cli`. Build config: `pyproject.toml` (PEP 621).
- Auth (simplest first): set `YANDEX_DIRECT_TOKEN` in `~/.claude/settings.json` env, or run `auth_login`/`auth_setup` (saved to `~/.direct-cli/auth.json`). `direct-cli` resolves explicit env creds before the active profile.
- Creds: `YANDEX_DIRECT_TOKEN`, `YANDEX_DIRECT_LOGIN`, `YANDEX_DIRECT_CLI_PATH`. Finance/master tokens are env-only: `YANDEX_DIRECT_FINANCE_TOKEN`, `YANDEX_DIRECT_MASTER_TOKEN`.
- Optional registration (`server/optional_tools.py`, default = none): `YANDEX_DIRECT_OPTIONAL_TOOLS` accepts `browser`, `trackingparams`, a comma-separated combination, or `all`. The import gate runs before tool-surface filtering, so profiles/groups can subtract tools after their bundle is loaded; surface allow-lists do not load bundles by themselves.
- Browser read deployment: `YANDEX_DIRECT_BROWSER_PROFILE_DIR` and `YANDEX_DIRECT_BROWSER_CHROME_PROFILE` select the Chrome profile; `YANDEX_DIRECT_BROWSER_HEADFUL=1` shows the browser. These are server env settings, not MCP tool parameters.
- Tool-surface selection (`server/config.py`, default = all 149 registered tools): `YANDEX_DIRECT_TOOL_PROFILE` (`full|core|analytics|campaign-editor`), `YANDEX_DIRECT_ENABLED_GROUPS`/`_DISABLED_GROUPS` (service / action / product-area / `financial`), `YANDEX_DIRECT_ENABLED_TOOLS`/`_DISABLED_TOOLS`.

## Tools

149 tools are registered by default (141 Direct API + 4 CLI helpers + 4 plugin); the contract reserves 23 browser/local-reference names for opt-in implementation modules, plus the `oauth_login` prompt. **Canonical list: `server/contract.py`**; default tables are in [docs/TOOLS.md](docs/TOOLS.md) — do not maintain a copy here. Each tool exposes a one-line description; call `tool_help('<name>')` for full docs (parameters, examples, constraints); `tool_help()` lists registered tools.

Transport-blocked (in WSDL/tapi, no `direct` subcommand — see `TRANSPORT_BLOCKED_OPERATIONS`):

| Operation | Reason |
|---|---|
| `dynamicads_update` | no CLI subcommand |
| `negativekeywords_*` | not a CLI service; use AdGroups payload or `negativekeywordsharedsets_*` |
| `bidmodifiers_toggle` | removed in CLI 0.2.8; API op deprecated 2025-11-13 |

## Browser-backed tools authentication

When present in `PUBLIC_CONTRACT`, Masters tools do not use the API OAuth path
described under Environment. Campaign Wizard has no Management API, so Masters
reads and lifecycle mutations invoke Playwright against the Direct web UI.
Check the installed build's `tool_help()` output before assuming they are
available. The browser's logged-in account is authoritative;
`YANDEX_DIRECT_TOKEN`, `YANDEX_DIRECT_LOGIN`, and the finance
`YANDEX_DIRECT_MASTER_TOKEN` do not authenticate or select an account for these
tools.

`history_get` is another read-only browser tool. It reads the account-wide
«История изменений» journal with server-side filters, automatic pagination, and
`Gtid` de-duplication for overlapping timestamp-cursor pages. Plain dates expand
to full-day boundaries in `direct`. For its `categories` filter, omission keeps
the web UI's complete category list, while an explicit empty string filters out
all records; callers must not collapse those two states.

The first optional thin slice also includes two zero-parameter helpers:

| Bundle | Tool | CLI command | Safety |
|---|---|---|---|
| `trackingparams` | `trackingparams_get` | `direct trackingparams` | Static local reference; no browser or API request |
| `browser` | `playwright_doctor` | `direct playwright doctor` | Read-only diagnostics; never logs in, launches a browser, or writes files |

CLI output controls and Playwright profile path/name are transport/deployment
configuration, not MCP inputs. Calibration on 2026-08-27 with deterministic
`approx(len/4)`: `OPTIONAL_TOOLS=all` registers 158 implemented tools / 33,987
tokens, while the two zero-parameter W-04 schemas contribute **136 tokens**
(`trackingparams_get` +63, `playwright_doctor` +73). This PR's incremental delta
is +73 because W-02 already landed `trackingparams_get`; the default surface
remains unchanged. The same two-tool delta is 113 with
`tiktoken/cl100k_base`.

Provision Masters authentication manually, outside the stdio MCP process:

1. From an interactive terminal running as the same OS user/`HOME` as the MCP
   server, install the `direct-cli[browser]` extra and Playwright Chromium if
   needed. Install the extra into the environment of the exact `direct`
   executable selected by the MCP server, pinned to that executable's currently
   installed `direct-cli` version. Do not redirect the server to an arbitrary
   unpinned system CLI; it is the transport for every plugin tool.
2. Run `direct masters login` and complete Yandex Passport login in the visible
   Chromium window. This creates the CLI-owned persistent profile at
   `~/.direct-cli/chrome-profile/`; it does not read the user's real Chrome
   profile or macOS Keychain.
3. Start or restart the MCP client, then enable the `browser` optional bundle
   and call the Masters tools exposed by that plugin version. Lifecycle tools
   change live campaign state: launch and archive have no CLI rollback. Copy is
   non-idempotent and always creates a draft; publish the clone separately via
   the lifecycle-gated `masters_launch` tool.

`direct masters login` requires a TTY, visible GUI session, and human input; do
not attempt it from a tool call, headless/remote process without GUI, CI, or an
ephemeral sandbox. Once provisioned, reads may run headlessly only while the
same home directory and Playwright Chromium remain available.

The alternative `direct playwright login` path imports Yandex cookies from a
real Chrome profile into `~/.direct-cli/playwright/session.json`; on macOS it
reads the `Chrome Safe Storage` key from the login Keychain. `direct playwright
doctor` diagnoses that path without logging in or writing files. A persistent
profile created by `direct masters login` takes precedence over the imported
session. Treat both stores as live login credentials; `direct masters logout`
removes the CLI-owned persistent profile.

## Testing

Three modes: **cassettes** (default `pytest`, recorded in `tests/recordings/`, no network), **mocks** (`-m mocks`, patch `subprocess.run` for unreproducible edges), **integration** (`-m integration`, live token). Cassette lifecycle: record → sanitize (strip secrets/PII) → audit → commit → replay. Some v2 tools (`advideos_*`, `*_set_auto`, `retargeting_update`) are mock-only pending cassette recording.

**Two cassette layers, two owners.** The plugin's `tests/recordings/` cassettes capture `direct` subprocess output (stdout/returncode) — that's this repo's responsibility, recorded via `pytest --record` against a live `direct` auth profile. HTTP-level API cassettes (VCR/yaml against Yandex.Direct itself) belong to `axisrow/direct-cli` (`tests/cassettes/`, recorded upstream) — the plugin never calls the live API to produce or refresh them, per the CLI-as-transport-boundary rule above. A tool with no plugin-level cassette but full CLI-level coverage is not blocked on this repo; gaps get filed upstream in `direct-cli`. There is no `.env.test` in this repo — local secrets live in `.env`, and live-mode auth resolves through `direct` profiles (`~/.direct-cli/auth.json`).

## Key Conventions

- **Money is micro-units**: 15 RUB = 15_000_000. CLI 0.2.10+ rejects `0 < x < 100_000` with a "× 1_000_000?" hint.
- **API batch limit: 10 IDs per request.** Some SelectionCriteria filters are stricter (dynamicads/smartadtargets `CampaignIds`=2, keywordbids=10); dry-run does not surface these.
- Runtime pin: `direct-cli==0.5.2` in `scripts/runtime-pins.env`; bump via `scripts/update-pins.sh`. Plugin version bumps via `scripts/update-version.sh` — never by hand (syncs both manifests + marketplace).
- `reports_custom(goal_ids=...)` adds `Conversions_<goal>_<attr>` / `CostPerConversion_<goal>_<attr>` columns; default attribution `LSC`.
- Docs in Russian, code identifiers in English.

## Dual-channel layout (do NOT consolidate)

Ships to two hosts, so manifests + `.mcp.json` deliberately exist twice — not a duplication bug.

| Channel | Manifest | MCP config | Launcher | Bootstrap |
|---|---|---|---|---|
| Claude Code | `.claude-plugin/plugin.json` | `.mcp.json` | `hooks/run-server.sh` | `hooks/setup.sh` (SessionStart hook) |
| Codex | `plugins/yandex-direct/.codex-plugin/plugin.json` | `plugins/yandex-direct/.mcp.json` | `plugins/yandex-direct/run-server.sh` | self-bootstrap in launcher (no SessionStart hook) |

The two `.mcp.json` differ only in the wrapper-script path; both omit `type` (stdio is implicit when `command` is present).
