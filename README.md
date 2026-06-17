# yandex-direct-mcp-plugin

Claude Code plugin for managing Yandex.Direct advertising campaigns.

## Project Status

The project is implemented and publicly available at
[`axisrow/yandex-direct-mcp-plugin`](https://github.com/axisrow/yandex-direct-mcp-plugin).
It packages a Python MCP server, Yandex.Direct domain skills, and OAuth helpers
around the `direct` CLI, which remains the only transport boundary to the
Yandex.Direct API.

Current distribution focus:

- keep the open-source MCP server and core skills free under the MIT license;
- publish installable plugin bundles for Claude Code and Codex-compatible
  environments;
- keep the README and generated docs strong enough for public onboarding, demos,
  and registry listings;
- reserve paid work for advanced analytics skills, agency integrations,
  white-label packaging, and consulting around Yandex.Direct automation.

## Features

- **MCP Server** — structured tools for campaigns, ads, keywords, and reports
- **Skills** — domain knowledge for Yandex.Direct management and ad copywriting
- **OAuth profiles** — authentication delegated to direct auth profiles with token + login stored together

## Architecture

```
direct (CLI executable; package: direct-cli) — низкоуровневая утилита (Python), общается с Яндекс.Директ API
       ↑
MCP Server (Python)     — обёртка над CLI, выставляет структурированные инструменты
       ↑
Skill (SKILL.md)        — доменные знания: когда какой инструмент вызвать, лимиты, подводные камни
       ↑
Plugin (.claude-plugin) — контейнер, объединяющий MCP + скиллы + OAuth в единый пакет
```

| Компонент | Что это | Что делает | Без него |
|---|---|---|---|
| **direct** (пакет `direct-cli`) | CLI-утилита (Python) | Выполняет запросы к Яндекс.Директ API | Ничего не работает |
| **MCP Server** | Процесс (stdio, Python) | Превращает CLI в структурированные инструменты с типизированными параметрами и ответами | Claude собирает bash-команды вручную |
| **Skill** | Markdown-файл | Учит Claude *когда* и *зачем* вызывать инструменты, хранит доменные знания | Claude не знает про лимиты API, батчинг, второй аккаунт |
| **Plugin** | Директория с манифестом | Упаковывает MCP + скиллы + OAuth для установки одной командой | Нужно настраивать каждый компонент отдельно |

## Installation

### Codex installable plugin

This repository now includes a Codex marketplace entry and installable plugin bundle:

- Marketplace manifest: `.agents/plugins/marketplace.json`
- Plugin bundle: `plugins/yandex-direct/.codex-plugin/plugin.json`

### Local development

```bash
# Run the MCP server directly from the repo
python -m server.main
```

### How the MCP server starts (Linux/macOS)

On `SessionStart` the `hooks/setup.sh` hook installs `mcp` and `direct-cli`.
On Debian/Ubuntu and other externally-managed Pythons (PEP 668) a plain
`pip install --user` is blocked, so dependencies go into a per-user
virtualenv at `${CLAUDE_PLUGIN_DATA}/venv` (default
`~/.claude/plugins/data/yandex-direct/venv`). On macOS they fall back to user
site-packages.

`.mcp.json` therefore does **not** launch the server with a bare `python3`
(the system interpreter would not see the venv on Linux). Instead it runs
`hooks/run-server.sh`, which prefers the venv interpreter and falls back to
system `python3`:

```jsonc
// .mcp.json
{ "mcpServers": { "yandex-direct-mcp": {
  "command": "bash",
  "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/run-server.sh"]
}}}
```

Troubleshooting (server fails to start / no tools):

- Confirm the venv exists and has deps:
  `~/.claude/plugins/data/yandex-direct/venv/bin/python3 -c "import mcp, direct_cli"`.
- If `CLAUDE_PLUGIN_DATA` is set to a volatile path (e.g. under `/tmp`), the
  venv is lost on reboot — point it at a stable per-user directory.
- You should not need to hardcode an absolute interpreter path in
  `settings.json`; the wrapper resolves it at launch.

## Authentication

Authentication is handled by `direct-cli`. The plugin does not store tokens;
all Direct API tools run `direct <command>` and let the CLI resolve token and
Client-Login from the active profile.

### OAuth login

Use `auth_login` for a fully interactive CLI-backed flow:
```
mcp__yandex_direct__auth_login()
```

### Direct token

You can also save a ready token; pass `login` when the token belongs to a
specific Yandex.Direct client login:
```
mcp__yandex_direct__auth_setup(code="y0_AgAAAA...", login="client-login")
```

### Token storage

Tokens are saved by `direct-cli` in its profile store, normally
`~/.direct-cli/auth.json`. The MCP plugin does not read that store directly:
`auth_status` delegates to `direct auth status --format json` so `direct`
remains the only auth boundary.

## Setup: Creating Yandex Applications

Для работы плагина нужно зарегистрировать **два приложения** в Яндексе:

### Шаг 1. OAuth-приложение (oauth.yandex.ru)

Это приложение получает OAuth-токены от имени пользователя.

1. Перейдите на https://oauth.yandex.ru/client/new
2. Заполните форму:
   - **Название** — любое (например, `My Direct Plugin`)
   - **Платформа** — выберите «Веб-сервисы»
   - **Redirect URI** — `https://oauth.yandex.ru/verification_code`
   - **Доступы** — обязательно добавьте **«Использование API Яндекс Директа»** (`direct:api`)
3. Нажмите «Создать приложение»
4. Скопируйте **Client ID** (ID приложения) и **Client Secret** (Пароль приложения)

### Шаг 2. Заявка на доступ к API Директа (direct.yandex.ru)

OAuth-приложение само по себе не даёт доступ к API — нужна отдельная заявка.

1. Войдите в https://direct.yandex.ru
2. Перейдите в **Инструменты → API → Мои заявки**
3. Нажмите «Новая заявка»
4. Укажите **Client ID** из Шага 1
5. Выберите уровень доступа (начните с тестового)
6. Отправьте заявку и дождитесь подтверждения

> **Без выполненного Шага 2** все запросы к API вернут ошибку `incomplete_registration` (код 58).

### Использование своего приложения

Если нужен собственный OAuth client, настройте его через `direct`:

```bash
direct auth login --client-id "ваш-client-id" --client-secret "ваш-client-secret"
```

### Язык вывода CLI (`--locale`)

`direct-cli` 0.4.0+ поддерживает глобальный флаг `--locale ru|en` (или
переменную окружения `YANDEX_DIRECT_CLI_LOCALE`) для языка справки и сообщений.
Это удобство уровня CLI: плагин использует значение по умолчанию и не
пробрасывает флаг, поэтому на работу MCP-инструментов он не влияет.

## MCP contract (146 tools)

The public contract is now defined as:

`MCP -> direct -> tapi-yandex-direct -> Yandex.Direct API`

- MCP never calls Yandex.Direct directly.
- `direct` remains the only execution/transport boundary.
- The package is installed as `direct-cli`; the runtime version floor lives in
  [`server/cli/runner.py`](server/cli/runner.py).
- `tapi-yandex-direct` naming is the default source reused by the CLI.
- WSDL / Reports spec wins when old CLI convenience names drift.
- v4 Live methods are exposed only when `direct` has a typed public command.

The machine-readable parity source lives in
[`server/contract.py`](server/contract.py).

### Configuring the tool surface (profiles & groups)

By default all 146 tools are exposed. The full spec (names + descriptions +
parameter schemas) is a fixed per-request cost, so you can narrow it to the
tools you actually use via environment variables. Resolution is deterministic:
`tool disabled > tool enabled > group disabled > group enabled > profile/default`.

| Env var | Effect |
|---|---|
| `YANDEX_DIRECT_TOOL_PROFILE` | preset: `full` (default), `core`, `analytics`, `campaign-editor` |
| `YANDEX_DIRECT_ENABLED_GROUPS` | allow-list mode: expose only these groups |
| `YANDEX_DIRECT_DISABLED_GROUPS` | subtract groups from the full surface |
| `YANDEX_DIRECT_ENABLED_TOOLS` / `YANDEX_DIRECT_DISABLED_TOOLS` | per-tool overrides (comma-separated) |

Groups are **service** names (`campaigns`, `ads`, …), **actions**
(`read` / `mutate` / `destructive` = delete only / `lifecycle` =
suspend·resume·archive·unarchive·moderate), **product areas** (`analytics`,
`campaign_management`, `bidding_budget`, `assets_creatives`,
`targeting_audience`), or the **risk** group `financial`
(money-movement `v4account_deposit` / `invoice` / `transfer_money`).
`auth_*` and `tool_help` stay available in every profile.

```jsonc
// ~/.claude/settings.json — analytics-only, read surface
{ "env": { "YANDEX_DIRECT_TOOL_PROFILE": "analytics" } }
```

Approximate budget by profile (share of full; see
[`docs/token-budget.md`](docs/token-budget.md)): `core` ~7% (10 tools),
`analytics` ~11% (28), `campaign-editor` ~49% (35), `full` 100% (146).
Disabled tools are absent from `tools/list`; unknown profile/group names log a
warning on stderr and fall back to the full surface.

### Naming rules

- Direct operations use canonical `service_method` names borrowed from the CLI:
  - `campaigns_get`, `ads_get`, `adgroups_get`
  - `agencyclients_get`, `audiencetargets_set_bids`
  - `keywordbids_set_auto`, `bids_set_auto`
- Old `*_list` names became `*_get`.
- Kebab CLI methods become snake_case in MCP:
  - `check-campaigns` → `changes_check_campaigns`
  - `check-dictionaries` → `changes_check_dictionaries`
  - `has-search-volume` → `keywordsresearch_has_search_volume`
  - `set-auto` → `*_set_auto`
  - `set-bids` → `*_set_bids`

### Surface classification

| Surface | Examples | Notes |
|---|---|---|
| Direct API tools | `campaigns_get`, `advideos_add`, `dictionaries_get_geo_regions`, `dynamicads_set_bids`, `balance_get`, `v4goals_get_stat_goals`, `v4tags_get_campaigns` | Canonical CLI-mediated Direct contract |
| CLI helper tools | `agencyclients_delete`, `dictionaries_list_names`, `reports_list_types` | Public, but explicitly not 1:1 Direct API methods |
| Plugin tools | `auth_status`, `auth_setup`, `auth_login`, `tool_help` | Plugin-only utilities, not Direct operations. `tool_help('<name>')` returns a tool's full docs on demand — tools expose only a one-line description to keep startup context small |

### Breaking-change migration highlights

| Old name | New name / status |
|---|---|
| `campaigns_list` | `campaigns_get` |
| `adgroups_list` | `adgroups_get` |
| `ads_list` | `ads_get` |
| `keyword_bids_*` | `keywordbids_*` |
| `audience_targets_*` | `audiencetargets_*` |
| `agency_clients_*` | `agencyclients_*` |
| `smart_ad_targets_*` | `smartadtargets_*` |
| `dynamic_ads_*` | `dynamicads_*` |
| `negative_keyword_shared_sets_*` | `negativekeywordsharedsets_*` |
| `changes_checkcamp` | `changes_check_campaigns` |
| `changes_checkdict` | `changes_check_dictionaries` |
| `keywords_has_volume` | `keywordsresearch_has_search_volume` |
| `keywords_deduplicate` | `keywordsresearch_deduplicate` |
| `turbo_pages_list` | `turbopages_get` |

#### Grouped dict params (token-budget, #220)

To shrink the JSON Schema of the widest mutate tools, families of flat params are
exposed as a single nested `dict` param (keys = the **old flat param names**, so
the underlying `direct` CLI call is unchanged). Migration for `ads_add` /
`ads_update`:

| Old flat params | New dict param (keys unchanged) |
|---|---|
| `price_extension_price`, `price_extension_old_price`, `price_extension_price_qualifier`, `price_extension_price_currency` | `price_extension_options={...}` |
| `video_extension_creative_id`, `video_extension_ids` | `video_extension_options={...}` |
| `callouts_add`, `callouts_remove`, `callouts_set` (ads_update) | `callouts_options={...}` |
| `creative_id`, `creative_erir_ad_description` (ads_update) | `creative_options={...}` |
| `title_sources`, `text_sources`, `default_texts` | `text_source_options={...}` |

Example: `ads_update(id=…, price_extension_options={"price_extension_price": "100"})`.
(In `ads_add`, `creative_id` stays a flat param and there are no callouts.)

Same migration for `campaigns_add` / `campaigns_update` (keys unchanged):

| Old flat params | New dict param |
|---|---|
| `notification_email`, `notification_check_position_interval`, `notification_warning_balance`, `notification_send_account_news`, `notification_send_warnings` | `notification_options={...}` |
| `time_targeting_schedule`, `consider_working_weekends`, `holidays_suspend_on_holidays`, `holidays_bid_percent`, `holidays_start_hour`, `holidays_end_hour` | `time_targeting_options={...}` |
| `frequency_cap_impressions`, `frequency_cap_period_days`, `frequency_cap_period_all` | `frequency_cap_options={...}` |
| `relevant_keywords_budget_percent`, `relevant_keywords_mode`, `relevant_keywords_optimize_goal_id` | `relevant_keywords_options={...}` |
| `package_platform_*` (7 flags) | `package_platform_options={...}` |
| `sms_events`, `sms_time_from`, `sms_time_to` | `sms_options={...}` |
| `search_placement_*` (3 flags) | `search_placement_options={...}` |
| `strategy_auto_continue`, `strategy_end_date`, `strategy_spend_limit`, `strategy_start_date` (CPM) | `cpm_strategy_options={...}` |

Small families (`attribution_model`, `package_strategy_*`, `dynamic_placement_*`)
stay flat. This is in addition to the bidding-strategy `*_options` dicts from #154.
| `dynamic_targets_*`, `smart_targets_*`, `negative_keywords_*` | removed legacy aliases |
| `turbo_pages_add`, `dynamic_ads_update` | removed from the public contract because current `direct` CLI does not expose them |

### Newly exposed CLI-backed operations

- `advideos_get`, `advideos_add`
- `agencyclients_update`
- `agencyclients_add_passport_organization`
- `agencyclients_add_passport_organization_member`
- `bidmodifiers_add`
- `bids_set_auto`
- `creatives_add`
- `dictionaries_get_geo_regions`
- `keywordbids_set_auto`
- `retargeting_update`
- `audiencetargets_set_bids`
- `dynamicads_suspend`, `dynamicads_resume`, `dynamicads_set_bids`
- `smartadtargets_suspend`, `smartadtargets_resume`, `smartadtargets_set_bids`
- `balance_get`
- `v4goals_get_stat_goals`, `v4goals_get_retargeting_goals`
- `v4tags_get_campaigns`, `v4tags_get_banners`
- `v4tags_update_campaigns`, `v4tags_update_banners`
- `v4account_get_accounts`, `v4account_update_account`, `v4account_deposit`, `v4account_invoice`, `v4account_transfer_money`, `v4account_enable_shared_account`
- `v4events_get_events_log`
- `v4wordstat_create_report`, `v4wordstat_list_reports`, `v4wordstat_get_report`, `v4wordstat_delete_report`

### v4 Live coverage

`direct-cli` 0.4.1 exposes typed v4 Live commands for the methods below. Only
typed public commands are registered as MCP tools. The single
``v4account account-management`` CLI subcommand drives five discrete MCP
tools (one per ``--action``) so financial mutations get isolated signatures
and finance/master tokens stay env-only:

- `direct balance` → `balance_get`
- `direct v4account account-management --action Get` → `v4account_get_accounts`
- `direct v4account account-management --action Update` → `v4account_update_account`
- `direct v4account account-management --action Deposit` → `v4account_deposit`
- `direct v4account account-management --action Invoice` → `v4account_invoice`
- `direct v4account account-management --action TransferMoney` → `v4account_transfer_money`
- `direct v4account enable-shared-account` → `v4account_enable_shared_account`
- `direct v4events get-events-log` → `v4events_get_events_log`
- `direct v4goals get-stat-goals` → `v4goals_get_stat_goals`
- `direct v4goals get-retargeting-goals` → `v4goals_get_retargeting_goals`
- `direct v4tags get-campaigns` → `v4tags_get_campaigns`
- `direct v4tags get-banners` → `v4tags_get_banners`
- `direct v4tags update-campaigns` → `v4tags_update_campaigns`
- `direct v4tags update-banners` → `v4tags_update_banners`
- `direct v4forecast create` → `v4forecast_create`
- `direct v4forecast list` → `v4forecast_list`
- `direct v4forecast get` → `v4forecast_get`
- `direct v4forecast delete` → `v4forecast_delete`
- `direct v4wordstat create-report` → `v4wordstat_create_report`
- `direct v4wordstat list-reports` → `v4wordstat_list_reports`
- `direct v4wordstat get-report` → `v4wordstat_get_report`
- `direct v4wordstat delete-report` → `v4wordstat_delete_report`
- `direct v4keywords get-suggestion` → `v4keywords_get_suggestion`
- `direct v4adimage get` → `v4adimage_get`
- `direct v4adimage set` → `v4adimage_set`

Other methods from `direct_cli.v4_contracts` are tracked in
`server/contract.py` as blocked/future metadata and are not exposed until the CLI
publishes typed commands for them. Standalone `v4finance` commands remain
blocked from the public MCP surface pending separate financial-operation gates.

## Skills

- `/yandex-direct:yandex-direct` — campaign management guidance
- `/yandex-direct:direct-ads` — ad copywriting for Yandex.Direct
- `/yandex-direct:direct-eda` — exploratory analysis of Direct statistics over reports

## Usage Examples

Just ask in natural language — the plugin handles the rest:

```
> покажи активные кампании
  → campaigns_get(state="ON")

> сколько объявлений в кампании 12345?
  → ads_get(campaign_ids="12345") → count

> отключи кампанию 67890
  → campaigns_update(id="67890", status="OFF")

> покажи ключевые слова кампании 12345
  → keywords_get(campaign_ids="12345")

> поставь ставку 15 руб на ключевое слово 99999
  → keywordbids_set(keyword_id=99999, search_bid=15000000)

> статистика за последнюю неделю
  → reports_get(date_from="2026-03-30", date_to="2026-04-06")

> баланс аккаунта
  → balance_get()

> цели Метрики для кампании 12345
  → v4goals_get_stat_goals(campaign_ids="12345")

> напиши объявление для доставки пиццы
  → /yandex-direct:direct-ads "доставка пиццы"

> токен живой?
  → auth_status()
```

### MCP Tool Calls

Direct MCP tool invocations that Claude makes under the hood:

```python
# Список активных кампаний
mcp__yandex_direct__campaigns_get(state="ON")
# → [{"Id": 12345, "Name": "Кампания 1", "State": "ON", "DailyBudget": 5000}, ...]

# Объявления в кампании
mcp__yandex_direct__ads_get(campaign_ids="12345")
# → [{"Id": 111, "Title": "Доставка пиццы", "Title2": "За 30 минут", "State": "ON"}, ...]

# Включить/отключить кампанию
mcp__yandex_direct__campaigns_update(id="67890", status="OFF")
# → {"success": True, "id": 67890, "status": "OFF"}

# Ключевые слова
mcp__yandex_direct__keywords_get(campaign_ids="12345")
# → [{"Id": 99999, "Keyword": "пицца доставка", "Bid": 12000000}, ...]

# Изменить ставку (в микроюнитах: 15 руб = 15000000)
mcp__yandex_direct__keywordbids_set(keyword_id=99999, search_bid=15000000)
# → {"success": True, "id": 99999, "bid": 15000000}

# Статистика
mcp__yandex_direct__reports_get(date_from="2026-03-30", date_to="2026-04-06")
# → [{"CampaignName": "Ретаргет ДРР 18.10", "Impressions": 15420, "Clicks": 312,
#     "Cost": 4680.50, "Conversions": 70, "CostPerConversion": 68.51,
#     "ConversionRate": 22.44}, ...]

# Статус direct auth profile
mcp__yandex_direct__auth_status()
# → {"valid": True, "profile": "default", "login": "ksamatadirect", "expires_in": 7200}

# Авторизация (первый раз)
mcp__yandex_direct__auth_login()
# → {"success": True, "method": "oauth_code", "profile": "default"}
```

### Error Handling

```python
# Токен истёк → `direct` обновит direct auth profile перед запросом
mcp__yandex_direct__campaigns_get(state="ON")
# MCP-плагин refresh не делает; transport и refresh принадлежат `direct`

# Токен или профиль невалиден
mcp__yandex_direct__campaigns_get(state="ON")
# → {"error": "auth_expired", "hint": "Run auth_status ... auth_login ..."}

# Обычный OAuth code передан не в тот flow
mcp__yandex_direct__auth_setup(code="0000000")
# → {"success": False, "error": "unsupported_oauth_code_flow", "hint": "Запустите auth_login() ..."}

# Кампания не найдена
mcp__yandex_direct__campaigns_update(id="999", status="ON")
# → {"error": "not_found", "message": "Кампания 999 не найдена в аккаунте ksamatadirect"}

# Кампания принадлежит второму аккаунту (ID ~73-77М)
mcp__yandex_direct__ads_get(campaign_ids="75000001")
# → {"error": "foreign_campaign", "message": "Кампания 75000001 недоступна — принадлежит другому аккаунту"}

# Лимит API (слишком много ID за раз)
mcp__yandex_direct__ads_get(campaign_ids="1,2,3,4,5,6,7,8,9,10,11")
# → {"error": "batch_limit", "message": "Максимум 10 ID за запрос. Передано: 11"}

# direct не установлен или не в PATH
mcp__yandex_direct__campaigns_get()
# → {"error": "cli_not_found", "message": "direct не найден. Установите пакет direct-cli и запускайте команду `direct`: https://github.com/axisrow/direct-cli"}

# Заявка на доступ к API не подана или отклонена (ошибка 58)
mcp__yandex_direct__campaigns_get()
# → {"error": "incomplete_registration", "message": "Незаконченная регистрация. Вам нужно подать или переподать заявку..."}
```

### Without plugin (before)

```bash
export BW_SESSION="$(bw unlock --raw)"
direct --bw-token-ref "yandex-direct" --bw-login-ref "yandex-direct" \
  campaigns get --format json | jq '.[] | select(.State == "ON")'
```

### With plugin (after)

```
> покажи активные кампании
```

## Testing

```bash
pytest
```

### Test Coverage

| # | Сценарий | Что проверяем | Ожидаемый результат |
|---|---|---|---|
| **Auth** |
| 1 | Обычный OAuth code отклоняется с подсказкой auth_login | `auth_setup(code=...)` без `y0_` | `{"success": False, "error": "unsupported_oauth_code_flow"}` |
| 2 | Интерактивный OAuth | `auth_login()` запускает pending PKCE flow и завершает его кодом через `direct` | `{"success": True, "method": "oauth_code"}` |
| 3 | Готовый токен | `auth_setup(code="y0_...", login="...")` | `{"success": True, "method": "direct_token"}` |
| 4 | Refresh токена | Запрос с истёкшим `access_token` | Refresh выполняет `direct` через активный direct auth profile |
| 5 | Refresh тоже протух | Профиль невалиден | `{"error": "auth_expired", "hint": "..."}` |
| 6 | Статус профиля | `auth_status()` | `{"valid": True/False, "profile", "login"}` |
| **Campaigns** |
| 7 | Список всех кампаний | `campaigns_get()` | Массив кампаний с Id, Name, State |
| 8 | Фильтр по статусу | `campaigns_get(state="ON")` | Только кампании с State=ON |
| 9 | Включить кампанию | `campaigns_update(id=..., status="ON")` | `{"success": True}` |
| 10 | Несуществующая кампания | `campaigns_update(id="999")` | `{"error": "not_found"}` |
| **Ads** |
| 11 | Объявления в кампании | `ads_get(campaign_ids="12345")` | Массив объявлений |
| 12 | Кампания второго аккаунта | `ads_get(campaign_ids="75000001")` | `{"error": "foreign_campaign"}` |
| 13 | Превышение лимита ID | `ads_get(campaign_ids="1,2,...,11")` | `{"error": "batch_limit"}` |
| **Keywords** |
| 14 | Ключевые слова | `keywords_get(campaign_ids="12345")` | Массив ключевых слов |
| 15 | Изменить ставку | `keywordbids_set(keyword_id=..., search_bid=...)` | `{"success": True}` |
| **Reports** |
| 16 | Статистика за период | `reports_get(date_from=..., date_to=...)` | Массив с CampaignName, Impressions, Clicks, Cost, Conversions |
| **Edge cases** |
| 17 | `direct` не в PATH | Запрос без установленного CLI | `{"error": "cli_not_found"}` |
| 18 | Пустой ответ API | Кампания без объявлений | `[]` (пустой массив, не ошибка) |
| 19 | Таймаут `direct` | CLI зависает >30с | `{"error": "timeout"}` |

### Test Structure

```
tests/
├── test_auth.py             # Тесты 1-6: OAuth flow
├── test_campaigns.py        # Тесты 7-10: кампании
├── test_ads.py              # Тесты 11-13: объявления
├── test_keywords.py         # Тесты 14-15: ключевые слова
├── test_reports.py          # Тест 16: отчёты
├── test_edge_cases.py       # Тесты 17-19: граничные случаи
├── cli_recorder.py          # Запись/воспроизведение CLI-вызовов
├── sanitize_cassettes.py    # Санитизация кассет
├── audit_cassettes.py       # Аудит кассет перед коммитом
├── conftest.py              # pytest fixtures, cli_recorder setup
├── fixtures/

### Live test suites

Live tests are split into read-only and mutating suites and are **disabled by default**.

```bash
# Read-only checks against the real API
pytest -m live_safe --run-live-safe

# Mutating checks with mandatory rollback
pytest -m live_unsafe --run-live-unsafe
```

`live_unsafe` requires dedicated test data in env vars:

```bash
TEST_OFF_CAMPAIGN_ID=123456
TEST_KEYWORD_CAMPAIGN_ID=123456
TEST_KEYWORD_ID=987654
TEST_KEYWORD_BID_TEMP=15000000
```

Do not point these at production entities. Unsafe tests assume the campaign starts in `OFF`, change it to `ON`, and then restore it. Keyword tests temporarily change the bid and then restore the original value.
│   ├── campaigns.json       # Мок-данные кампаний
│   └── ads.json             # Мок-данные объявлений
└── recordings/              # Записанные кассеты (коммитятся)
    ├── auth/
    │   ├── token-exchange.json
    │   ├── token-refresh.json
    │   └── invalid-code.json
    ├── campaigns/
    │   ├── list-all.json
    │   ├── list-active.json
    │   └── update-state.json
    ├── ads/
    │   ├── list-by-campaign.json
    │   └── foreign-campaign.json
    ├── keywords/
    │   └── list-and-update.json
    └── reports/
        └── weekly-stats.json
```

### Cassette Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│  ЗАПИСЬ (один раз, разработчик)                                 │
│                                                                 │
│  python -m tests.setup                                          │
│       │                                                         │
│       ▼                                                         │
│  .env.test ← живой OAuth-токен          ⛔ gitignored           │
│       │                                                         │
│       ▼                                                         │
│  pytest --record                                                │
│       │                                                         │
│       ▼                                                         │
│  direct ──→ Яндекс API ──→ сырые ответы                        │
│       │          (с токенами, названиями кампаний, ставками)     │
│       │                                                         │
│       ▼                                                         │
│  python -m tests.sanitize                                       │
│       │  • access_token → REDACTED                              │
│       │  • "Доставка пиццы" → "Campaign_12345"                  │
│       │  • ksamatadirect → test_account                         │
│       │  • 4680.50 → 1000.00                                    │
│       │                                                         │
│       ▼                                                         │
│  tests/recordings/*.json ← чистые кассеты  ✅ коммитятся в git  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ТЕСТЫ (каждый день, CI, любой разработчик)                     │
│                                                                 │
│  pytest                                                         │
│       │                                                         │
│       ▼                                                         │
│  tests/recordings/*.json → cli_recorder подставляет ответы      │
│       │                                                         │
│       │  Токен не нужен. Сеть не нужна. API не вызывается.      │
│       │                                                         │
│       ▼                                                         │
│  ✅ 19 тестов проходят                                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ЗАЩИТА (pre-commit + CI)                                       │
│                                                                 │
│  git commit                                                     │
│       │                                                         │
│       ▼                                                         │
│  python -m tests.audit сканирует tests/recordings/              │
│       │  Ищет: AQAAAA*, Bearer ey*, реальные домены, телефоны   │
│       │                                                         │
│       ├─ чисто → ✅ коммит проходит                             │
│       └─ нашёл утечку → ⛔ коммит блокируется                   │
└─────────────────────────────────────────────────────────────────┘
```

### Test Modes

**1. Cassettes (recorded CLI responses)** — основной режим

```bash
# Записать кассеты с реального API (один раз)
pytest --record

# Прогнать тесты на записанных кассетах (CI/повседневно)
pytest
```

**Recorder: собственный cli_recorder.py**

`direct` запускается как subprocess (после установки пакета `direct-cli`) — HTTP-рекордеры (nock, polly, responses, vcrpy) работают только in-process и его запросы не перехватят. Поэтому записываем на уровне CLI:

```
┌──────────────┐            ┌──────────────┐         ┌──────────────┐
│  MCP Server  │──subprocess──▶│    direct    │──HTTP──▶│  Яндекс API  │
│  (Python)    │◀──stdout─────│  (Python)    │◀────────│              │
└──────────────┘            └──────────────┘         └──────────────┘
       │
       ▼
  cli_recorder.py перехватывает:
  • args[]     — с какими аргументами вызван CLI
  • stdout     — что CLI вернул (JSON)
  • stderr     — ошибки
  • returncode — код возврата
```

Принцип работы:
1. **Режим записи** (`RECORD=true`): MCP-сервер вызывает реальный `direct`, `cli_recorder.py` сохраняет пару `{args, stdout, stderr, returncode}` в JSON-файл
2. **Режим воспроизведения** (по умолчанию): `unittest.mock.patch("subprocess.run")` подставляет мок, который ищет совпадение по `args` в записанных кассетах и возвращает сохранённый `stdout`
3. Санитизация прогоняется **между** шагами 1 и 2

```python
# tests/cli_recorder.py
class CliRecorder:
    def record(self, command: str, args: list[str]) -> dict:
        """Вызывает реальный CLI, сохраняет {args, stdout, stderr, returncode}"""
        result = subprocess.run([command, *args], capture_output=True, text=True)
        cassette = {"args": args, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
        self._save(cassette)
        return cassette

    def replay(self, command: str, args: list[str]) -> subprocess.CompletedProcess:
        """По args находит кассету, возвращает сохранённый stdout"""
        cassette = self._find(args)
        return subprocess.CompletedProcess(args, cassette["returncode"], cassette["stdout"], cassette["stderr"])
```

Кассета выглядит так:
```json
{
  "command": "direct",
  "args": ["campaigns", "get", "--format", "json"],
  "stdout": "[{\"Id\": 12345, \"Name\": \"Campaign_12345\", \"State\": \"ON\"}]",
  "stderr": "",
  "returncode": 0
}
```

**2. Mocks** — для edge cases, которые нельзя записать

```bash
pytest -m mocks
```

Моки через `unittest.mock.patch("subprocess.run")` только для сценариев, которых невозможно добиться от реального API:
- `cli_not_found` — исполняемый файл `direct` не установлен (`FileNotFoundError`)
- `timeout` — CLI зависает >30с (`subprocess.TimeoutExpired`)
- `batch_limit` — валидация на стороне MCP-сервера, до вызова API

**3. Integration (live API)** — перед релизом

```bash
# Требует валидный OAuth-токен
pytest -m integration
```

Полный прогон через реальный API Яндекс.Директ. Используется для:
- Верификации кассет (не устарели ли?)
- Обновления записей: `pytest --record`
- Smoke-тестов перед новой версией

### Cassette Sanitization

Кассеты содержат ответы реального API — **перед коммитом обязательна санитизация**. Скрипт `python -m tests.sanitize` прогоняется автоматически после записи и как pre-commit hook.

#### Что маскируется

| Поле | Пример до | После |
|---|---|---|
| `access_token` | `AQAAAACy1C6ZAAAAfa6v...` | `ACCESS_TOKEN_REDACTED` |
| `refresh_token` | `1:GN686QVt0mmak...` | `REFRESH_TOKEN_REDACTED` |
| `Authorization` header | `Bearer AQAAAACy1...` | `Bearer ACCESS_TOKEN_REDACTED` |
| `client_secret` | `a1b2c3d4e5f6` | `CLIENT_SECRET_REDACTED` |
| `client_id` | `abc123def456` | `CLIENT_ID_REDACTED` |

#### Что анонимизируется (коммерческие данные)

| Поле | Пример до | После |
|---|---|---|
| Названия кампаний | `Доставка пиццы Москва` | `Campaign_12345` |
| Тексты объявлений | `Закажите пиццу за 30 мин` | `Ad title for campaign 12345` |
| Ключевые слова | `пицца доставка москва` | `keyword_99999` |
| Логин аккаунта | `ksamatadirect` | `test_account` |
| Суммы расходов | `4680.50` | `1000.00` |
| URL сайтов в объявлениях | `https://pizza-example.ru` | `https://example.com` |
| Телефоны, адреса | `+7 (495) 123-45-67` | `+7 (000) 000-00-00` |

#### Как это работает

```python
# tests/sanitize_cassettes.py
import re
from pathlib import Path

SANITIZE_RULES = [
    # Секреты — полная замена
    (r'"access_token"\s*:\s*"[^"]+"',    '"access_token": "ACCESS_TOKEN_REDACTED"'),
    (r'"refresh_token"\s*:\s*"[^"]+"',   '"refresh_token": "REFRESH_TOKEN_REDACTED"'),
    (r'Bearer [A-Za-z0-9_-]+',           'Bearer ACCESS_TOKEN_REDACTED'),
    (r'"client_secret"\s*:\s*"[^"]+"',   '"client_secret": "CLIENT_SECRET_REDACTED"'),
    (r'"client_id"\s*:\s*"[^"]+"',       '"client_id": "CLIENT_ID_REDACTED"'),
    # Коммерческие данные — подмена на заглушки
    (r'"Name"\s*:\s*"[^"]+"',            '"Name": "Campaign_XXXXX"'),
    (r'"Title"\s*:\s*"[^"]+"',           '"Title": "Ad title placeholder"'),
    (r'"Title2"\s*:\s*"[^"]+"',          '"Title2": "Ad title2 placeholder"'),
    (r'"Keyword"\s*:\s*"[^"]+"',         '"Keyword": "keyword_XXXXX"'),
    (r'"Login"\s*:\s*"[^"]+"',           '"Login": "test_account"'),
    (r'"Cost"\s*:\s*[\d.]+',             '"Cost": 1000.00'),
    (r'"Href"\s*:\s*"https?://[^"]+"',   '"Href": "https://example.com"'),
    (r'\+7\s*\(?\d{3}\)?\s*\d{3}[\s-]?\d{2}[\s-]?\d{2}', '+7 (000) 000-00-00'),
]

def sanitize(recordings_dir: Path):
    for cassette in recordings_dir.rglob("*.json"):
        text = cassette.read_text()
        for pattern, replacement in SANITIZE_RULES:
            text = re.sub(pattern, replacement, text)
        cassette.write_text(text)
```

### Cassette Audit Specification

`python -m tests.audit` сканирует все файлы в `tests/recordings/` и проверяет:

#### 1. Секреты (CRITICAL — блокирует коммит)

| Что ищем | Regex | Пример утечки |
|---|---|---|
| OAuth-токен Яндекса | `AQAAAA[A-Za-z0-9_-]{20,}` | `AQAAAACy1C6ZAAAAfa6vDLu...` |
| Bearer-токен | `Bearer\s+[A-Za-z0-9_-]{20,}` | `Bearer AQAAAACy1C6Z...` |
| Refresh-токен | `\d+:[A-Za-z0-9_-]{10,}:` | `1:GN686QVt0mmak...` |
| Client secret | `"client_secret"\s*:\s*"[^"]{6,}"` | `"client_secret": "a1b2c3"` |
| Client ID (реальный) | Сверка с `YANDEX_CLIENT_ID` из `.env.test.example` | Совпадение → утечка |
| Base64 credentials | `Basic\s+[A-Za-z0-9+/=]{20,}` | `Basic YWJjMTIz...` |

#### 2. Коммерческие данные (WARNING — блокирует коммит)

| Что ищем | Regex | Пример утечки |
|---|---|---|
| Реальные домены | `https?://(?!example\.com)[a-z0-9.-]+\.[a-z]{2,}` | `https://pizza-shop.ru` |
| Телефоны | `\+7\s*\(?\d{3}\)?\s*\d{3}[\s-]?\d{2}[\s-]?\d{2}` | `+7 (495) 123-45-67` |
| Email-адреса | `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` | `manager@company.ru` |
| ИНН | `"\bInn\b".*\b\d{10,12}\b` | `"Inn": "7707083893"` |
| Логин аккаунта | Сверка с `YANDEX_LOGIN` из `.env.test.example` | `ksamatadirect` |

#### 3. Структурная валидация (INFO)

| Проверка | Что значит |
|---|---|
| Все кассеты — валидный JSON | Не битый файл |
| Каждая кассета содержит `args`, `stdout`, `returncode` | Полная запись |
| `stdout` парсится как JSON | CLI вернул структурированный ответ |
| Нет кассет > 1 MB | Подозрительно большой ответ |

#### Реализация

```python
# tests/audit_cassettes.py
import re, json, sys
from pathlib import Path

CRITICAL_PATTERNS = [
    (r"AQAAAA[A-Za-z0-9_-]{20,}",              "OAuth token"),
    (r"Bearer\s+[A-Za-z0-9_-]{20,}",           "Bearer token"),
    (r"\d+:[A-Za-z0-9_-]{10,}:",               "Refresh token"),
    (r'"client_secret"\s*:\s*"[^"]{6,}"',       "Client secret"),
    (r"Basic\s+[A-Za-z0-9+/=]{20,}",           "Base64 credentials"),
]

WARNING_PATTERNS = [
    (r'https?://(?!example\.com)[a-z0-9.-]+\.[a-z]{2,}', "Real domain"),
    (r'\+7\s*\(?\d{3}\)?\s*\d{3}[\s-]?\d{2}[\s-]?\d{2}', "Phone number"),
    (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', "Email address"),
]

def audit(recordings_dir: Path) -> int:
    critical, warnings = 0, 0
    for cassette in sorted(recordings_dir.rglob("*.json")):
        text = cassette.read_text()
        rel = cassette.relative_to(recordings_dir)

        # Структурная валидация
        try:
            data = json.loads(text)
            for key in ("args", "stdout", "returncode"):
                assert key in data, f"Missing key: {key}"
        except (json.JSONDecodeError, AssertionError) as e:
            print(f"  {rel}  ℹ️  INFO: {e}")

        # Секреты
        for pattern, label in CRITICAL_PATTERNS:
            match = re.search(pattern, text)
            if match:
                print(f"  {rel}  ⛔ CRITICAL: {label} found (pos {match.start()})")
                critical += 1

        # Коммерческие данные
        for pattern, label in WARNING_PATTERNS:
            match = re.search(pattern, text)
            if match:
                print(f"  {rel}  ⚠️  WARNING: {label} \"{match.group()[:40]}\" found")
                warnings += 1

        if not critical and not warnings:
            print(f"  {rel}  ✅ clean")

    print(f"\nResult: {critical} CRITICAL, {warnings} WARNING")
    if critical:
        print("⛔ Commit blocked. Run: python -m tests.sanitize")
        return 2
    if warnings:
        print("⚠️  Commit blocked. Run: python -m tests.sanitize")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(audit(Path("tests/recordings")))
```

#### Пример вывода

```
$ python -m tests.audit

Scanning tests/recordings/...
  auth/token-exchange.json     ✅ clean
  auth/token-refresh.json      ✅ clean
  campaigns/list-all.json      ✅ clean
  ads/list-by-campaign.json    ⛔ CRITICAL: OAuth token found (pos 342)
  ads/foreign-campaign.json    ⚠️  WARNING: Real domain "pizza-shop.ru" found
  reports/weekly-stats.json    ✅ clean

Result: 1 CRITICAL, 1 WARNING, 4 clean
⛔ Commit blocked. Run: python -m tests.sanitize
```

#### Exit codes

| Code | Значение |
|---|---|
| 0 | Все кассеты чисты |
| 1 | WARNING — коммерческие данные |
| 2 | CRITICAL — секреты |

#### CI integration

```yaml
# .github/workflows/cassette-audit.yml
- name: Audit cassettes
  run: python -m tests.audit
```

### Cassette Recording Rules

| Правило | Почему |
|---|---|
| Кассеты коммитятся в git | Тесты работают без API-ключей |
| Санитизация автоматическая (post-record + pre-commit) | Человек забудет, скрипт — нет |
| CI аудит кассет на каждый PR | Двойная проверка, ничего не утечёт |
| Коммерческие данные анонимизируются | Названия кампаний, тексты объявлений — конфиденциально |
| Кассеты перезаписываются перед мажорным релизом | Актуальность |
| Edge cases остаются моками | Невоспроизводимы через API |
| direct auth profile создаётся интерактивно | См. ниже |

### Setup for Recording

direct auth profile нужен **только для записи кассет** — обычный `pytest` работает без него.

```bash
# 1. Запустить скрипт настройки (интерактивно)
python -m tests.setup
```

Скрипт `tests.setup` делегирует авторизацию в CLI:

```bash
direct auth login
```

После этого профиль сохраняется в `~/.direct-cli/auth.json`. Дальше
`pytest --record` использует активный профиль CLI, записывает кассеты и сразу
прогоняет санитизацию.

**Итого: `pytest` не требует токенов. Профиль нужен только для `--record`, и скрипт запускает CLI-flow.**

## Tech Stack

| Слой | Технология | Версия | Зачем |
|---|---|---|---|
| **Runtime** | Python | >= 3.11 | Единый язык с direct-cli |
| **MCP Server** | [mcp](https://pypi.org/project/mcp/) | latest | Python SDK для MCP (stdio transport) |
| **CLI** | `direct` ([package: direct-cli](https://github.com/axisrow/direct-cli)) | latest | Обёртка над Яндекс.Директ API |
| **Testing** | [pytest](https://docs.pytest.org/) | >= 8.0 | Тесты, fixtures, markers |
| **Mocking** | `unittest.mock` | stdlib | Моки subprocess для edge cases |
| **Cassettes** | `cli_recorder.py` (свой) | — | Запись/воспроизведение CLI stdin/stdout |
| **Build** | [pyproject.toml](https://packaging.python.org/) | PEP 621 | Зависимости, scripts, metadata |
| **Linting** | [ruff](https://docs.astral.sh/ruff/) | latest | Линтинг + форматирование |
| **Types** | [mypy](https://mypy-lang.org/) | latest | Статическая типизация |
| **CI** | GitHub Actions | — | pytest + audit кассет |
| **Pre-commit** | [pre-commit](https://pre-commit.com/) | latest | Аудит кассет, ruff, mypy |

### What is NOT in the stack

| Технология | Почему нет |
|---|---|
| Node.js / npm | direct-cli — Python, MCP SDK — Python, нет смысла тащить второй runtime |
| nock / polly.js / vcrpy | HTTP-рекордеры не перехватывают subprocess — используем свой cli_recorder |
| Jest | Python-проект → pytest |
| Docker | Плагин ставится как директория, не нужен контейнер |
| Bitwarden | Поддержка секретов остаётся на стороне `direct-cli`, MCP-плагин их не читает |

### pyproject.toml

```toml
[project]
name = "yandex-direct-mcp-plugin"
version = "0.2.3"
requires-python = ">=3.11"
dependencies = [
    "mcp",
    "direct-cli>=0.4.3",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "ruff",
    "mypy",
    "pre-commit",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "mocks: edge case tests using unittest.mock",
    "integration: live API tests requiring OAuth token",
]

[tool.ruff]
target-version = "py311"
```

## License

MIT
