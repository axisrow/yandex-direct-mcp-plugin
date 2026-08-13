# CLAUDE.md

Claude Code plugin for managing Yandex.Direct advertising campaigns. Wraps the `direct` Python CLI via an MCP server (FastMCP, stdio); auth delegated to `direct` auth profiles. **Status:** Implemented.

## Architecture

```
MCP (server/main.py) → direct CLI → tapi-yandex-direct → Yandex.Direct API
```

- **MCP never calls Yandex.Direct directly** — always through `direct`, even to work around a missing/broken CLI feature. No `urllib`, raw HTTP, or `tapi-yandex-direct` imports. File upstream issues in `axisrow/direct-cli` and wait for the release.
- `direct` is the only execution/transport boundary. WSDL/Reports spec wins when CLI convenience names drift.
- Machine-readable parity source: `server/contract.py` (`PUBLIC_CONTRACT`, `TRANSPORT_BLOCKED_OPERATIONS`, `RENAMED_TOOL_MIGRATION`).
- `server/cli/runner.py` — `DirectCliRunner` subprocess wrapper. `server/tools/*.py` — 148 tools across 41 modules, one module per service. `server/tools/helpers.py` — shared validation (`parse_ids`, `check_batch_limit`).

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
- Tool-surface selection (`server/config.py`, default = all 148): `YANDEX_DIRECT_TOOL_PROFILE` (`full|core|analytics|campaign-editor`), `YANDEX_DIRECT_ENABLED_GROUPS`/`_DISABLED_GROUPS` (service / action / product-area / `financial`), `YANDEX_DIRECT_ENABLED_TOOLS`/`_DISABLED_TOOLS`.

## Tools

148 tools total (141 Direct API + 3 CLI helpers + 4 plugin) + the `oauth_login` prompt. **Canonical list: `server/contract.py`**; full tables in [docs/TOOLS.md](docs/TOOLS.md) — do not maintain a copy here. Each tool exposes a one-line description; call `tool_help('<name>')` for full docs (parameters, examples, constraints); `tool_help()` lists all.

Transport-blocked (in WSDL/tapi, no `direct` subcommand — see `TRANSPORT_BLOCKED_OPERATIONS`):

| Operation | Reason |
|---|---|
| `dynamicads_update` | no CLI subcommand |
| `negativekeywords_*` | not a CLI service; use AdGroups payload or `negativekeywordsharedsets_*` |
| `bidmodifiers_toggle` | removed in CLI 0.2.8; API op deprecated 2025-11-13 |

## Testing

Three modes: **cassettes** (default `pytest`, recorded in `tests/recordings/`, no network), **mocks** (`-m mocks`, patch `subprocess.run` for unreproducible edges), **integration** (`-m integration`, live token). Cassette lifecycle: record → sanitize (strip secrets/PII) → audit → commit → replay. Some v2 tools (`advideos_*`, `*_set_auto`, `retargeting_update`) are mock-only pending cassette recording.

**Two cassette layers, two owners.** The plugin's `tests/recordings/` cassettes capture `direct` subprocess output (stdout/returncode) — that's this repo's responsibility, recorded via `pytest --record` against a live `direct` auth profile. HTTP-level API cassettes (VCR/yaml against Yandex.Direct itself) belong to `axisrow/direct-cli` (`tests/cassettes/`, recorded upstream) — the plugin never calls the live API to produce or refresh them, per the CLI-as-transport-boundary rule above. A tool with no plugin-level cassette but full CLI-level coverage is not blocked on this repo; gaps get filed upstream in `direct-cli`. There is no `.env.test` in this repo — local secrets live in `.env`, and live-mode auth resolves through `direct` profiles (`~/.direct-cli/auth.json`).

## Key Conventions

- **Money is micro-units**: 15 RUB = 15_000_000. CLI 0.2.10+ rejects `0 < x < 100_000` with a "× 1_000_000?" hint.
- **API batch limit: 10 IDs per request.** Some SelectionCriteria filters are stricter (dynamicads/smartadtargets `CampaignIds`=2, keywordbids=10); dry-run does not surface these.
- Runtime pin: `direct-cli==0.4.3` in `scripts/runtime-pins.env`; bump via `scripts/update-pins.sh`. Plugin version bumps via `scripts/update-version.sh` — never by hand (syncs both manifests + marketplace).
- `reports_custom(goal_ids=...)` adds `Conversions_<goal>_<attr>` / `CostPerConversion_<goal>_<attr>` columns; default attribution `LSC`.
- Docs in Russian, code identifiers in English.

## Dual-channel layout (do NOT consolidate)

Ships to two hosts, so manifests + `.mcp.json` deliberately exist twice — not a duplication bug.

| Channel | Manifest | MCP config | Launcher | Bootstrap |
|---|---|---|---|---|
| Claude Code | `.claude-plugin/plugin.json` | `.mcp.json` | `hooks/run-server.sh` | `hooks/setup.sh` (SessionStart hook) |
| Codex | `plugins/yandex-direct/.codex-plugin/plugin.json` | `plugins/yandex-direct/.mcp.json` | `plugins/yandex-direct/run-server.sh` | self-bootstrap in launcher (no SessionStart hook) |

The two `.mcp.json` differ only in the wrapper-script path; both omit `type` (stdio is implicit when `command` is present).
