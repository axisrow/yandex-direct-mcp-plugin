# yandex-direct-mcp-plugin

Claude Code plugin for managing Yandex.Direct advertising campaigns.

## Features

- **MCP Server** — structured tools for campaigns, ads, keywords, and reports
- **Skills** — domain knowledge for Yandex.Direct management and ad copywriting
- **OAuth 2.0** — automatic token management with refresh support (no Bitwarden dependency)

## Architecture

```
direct-cli (CLI)        — низкоуровневая утилита (Python), общается с Яндекс.Директ API
       ↑
MCP Server (Python)     — обёртка над CLI, выставляет структурированные инструменты
       ↑
Skill (SKILL.md)        — доменные знания: когда какой инструмент вызвать, лимиты, подводные камни
       ↑
Plugin (.claude-plugin) — контейнер, объединяющий MCP + скиллы + OAuth в единый пакет
```

| Компонент | Что это | Что делает | Без него |
|---|---|---|---|
| **direct-cli** | CLI-утилита (Python) | Выполняет запросы к Яндекс.Директ API | Ничего не работает |
| **MCP Server** | Процесс (stdio, Python) | Превращает CLI в структурированные инструменты с типизированными параметрами и ответами | Claude собирает bash-команды вручную |
| **Skill** | Markdown-файл | Учит Claude *когда* и *зачем* вызывать инструменты, хранит доменные знания | Claude не знает про лимиты API, батчинг, второй аккаунт |
| **Plugin** | Директория с манифестом | Упаковывает MCP + скиллы + OAuth для установки одной командой | Нужно настраивать каждый компонент отдельно |

## Installation

```bash
# From local path (development)
claude --plugin-dir ./yandex-direct-mcp-plugin

# From GitHub
/plugin marketplace add axisrow/yandex-direct-mcp-plugin
/plugin install yandex-direct@axisrow-yandex-direct-mcp-plugin
```

## Authentication

Four ways to authenticate, from simplest to advanced:

### 1. Environment variable (recommended)

Add to `~/.claude/settings.json`:
```json
{
  "env": {
    "YANDEX_DIRECT_TOKEN": "y0_AgAAAA..."
  }
}
```
Restart Claude Code. Done.

### 2. Plugin settings

Set `token` in plugin configuration — will be available as `CLAUDE_PLUGIN_OPTION_token`.

### 3. OAuth PKCE (interactive)

No configuration needed. Use `auth_login` for a fully interactive flow (opens browser, prompts for code):
```
mcp__yandex_direct__auth_login()
```

Or manually with `auth_setup`:
```
mcp__yandex_direct__auth_setup(code="nvyaod2jwwf2ctyu")
```
Uses built-in OAuth app. No `client_secret` required. Token is saved to disk and auto-refreshed.

### 4. Custom OAuth app

For advanced users with their own registered Yandex OAuth app. Set `client_id` and `client_secret` in plugin settings — disables PKCE, uses classic OAuth flow.

### Direct token via auth_setup

You can also paste a token directly:
```
mcp__yandex_direct__auth_setup(code="y0_AgAAAA...")
```

### Token storage

OAuth tokens are saved to `$CLAUDE_PLUGIN_DATA/tokens.json`. The directory name depends on how the plugin was installed:

| Install method | Data directory |
|---|---|
| Marketplace (`/plugin install`) | `~/.claude/plugins/data/yandex-direct/` |
| Local path (`claude plugin install ./path`) | `~/.claude/plugins/data/yandex-direct-inline/` |

The `-inline` suffix is added by Claude Code for locally-installed plugins. The `$CLAUDE_PLUGIN_DATA` env var always points to the correct path, so this is transparent to the plugin.

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

После регистрации передайте credentials через настройки плагина:

```json
{
  "options": {
    "client_id": "ваш-client-id",
    "client_secret": "ваш-client-secret"
  }
}
```

Или через переменные окружения `CLAUDE_PLUGIN_OPTION_client_id` / `CLAUDE_PLUGIN_OPTION_client_secret`.

## MCP Tools

| Tool | Description |
|---|---|
| `campaigns_list` | List campaigns (filter by state) |
| `campaigns_update` | Enable/disable campaigns |
| `ads_list` | List ads in a campaign |
| `keywords_list` | List keywords in a campaign |
| `keywords_update` | Update keyword bids |
| `reports_get` | Get campaign statistics |
| `auth_status` | Check OAuth token status |
| `auth_setup` | Submit authorization code or direct token |
| `auth_login` | Interactive OAuth flow (browser + code input via elicitation) |

## Skills

- `/yandex-direct:yandex-direct` — campaign management guidance
- `/yandex-direct:direct-ads` — ad copywriting for Yandex.Direct

## Usage Examples

Just ask in natural language — the plugin handles the rest:

```
> покажи активные кампании
  → campaigns_list(state="ON")

> сколько объявлений в кампании 12345?
  → ads_list(campaign_ids="12345") → count

> отключи кампанию 67890
  → campaigns_update(id="67890", state="OFF")

> покажи ключевые слова кампании 12345
  → keywords_list(campaign_ids="12345")

> поставь ставку 15 руб на ключевое слово 99999
  → keywords_update(id="99999", bid="15000000")

> статистика за последнюю неделю
  → reports_get(date_from="2026-03-30", date_to="2026-04-06")

> напиши объявление для доставки пиццы
  → /yandex-direct:direct-ads "доставка пиццы"

> токен живой?
  → auth_status()
```

### MCP Tool Calls

Direct MCP tool invocations that Claude makes under the hood:

```python
# Список активных кампаний
mcp__yandex_direct__campaigns_list(state="ON")
# → [{"Id": 12345, "Name": "Кампания 1", "State": "ON", "DailyBudget": 5000}, ...]

# Объявления в кампании
mcp__yandex_direct__ads_list(campaign_ids="12345")
# → [{"Id": 111, "Title": "Доставка пиццы", "Title2": "За 30 минут", "State": "ON"}, ...]

# Включить/отключить кампанию
mcp__yandex_direct__campaigns_update(id="67890", state="OFF")
# → {"success": True, "id": 67890, "state": "OFF"}

# Ключевые слова
mcp__yandex_direct__keywords_list(campaign_ids="12345")
# → [{"Id": 99999, "Keyword": "пицца доставка", "Bid": 12000000}, ...]

# Изменить ставку (в микроюнитах: 15 руб = 15000000)
mcp__yandex_direct__keywords_update(id="99999", bid="15000000")
# → {"success": True, "id": 99999, "bid": 15000000}

# Статистика
mcp__yandex_direct__reports_get(date_from="2026-03-30", date_to="2026-04-06")
# → [{"CampaignName": "Ретаргет ДРР 18.10", "Impressions": 15420, "Clicks": 312,
#     "Cost": 4680.50, "Conversions": 70, "CostPerConversion": 68.51,
#     "ConversionRate": 22.44}, ...]

# Статус OAuth-токена
mcp__yandex_direct__auth_status()
# → {"valid": True, "expires_in": 7200, "scope": "direct:...", "login": "ksamatadirect"}

# Авторизация (первый раз)
mcp__yandex_direct__auth_setup(code="1234567")
# → {"success": True, "access_token": "AQA...", "expires_in": 124234123534}
```

### Error Handling

```python
# Токен истёк → MCP-сервер обновит автоматически через refresh_token
mcp__yandex_direct__campaigns_list(state="ON")
# 1) access_token expired → POST /token {grant_type: "refresh_token"}
# 2) новый access_token сохранён → повторный запрос → результат

# Токен невалиден (refresh тоже протух)
mcp__yandex_direct__campaigns_list(state="ON")
# → {"error": "auth_expired", "message": "Требуется повторная авторизация",
#    "auth_url": "https://oauth.yandex.ru/authorize?client_id=..."}

# Неверный код авторизации
mcp__yandex_direct__auth_setup(code="0000000")
# → {"error": "invalid_grant", "message": "Неверный или просроченный код. Код действует 10 минут."}

# Кампания не найдена
mcp__yandex_direct__campaigns_update(id="999", state="ON")
# → {"error": "not_found", "message": "Кампания 999 не найдена в аккаунте ksamatadirect"}

# Кампания принадлежит второму аккаунту (ID ~73-77М)
mcp__yandex_direct__ads_list(campaign_ids="75000001")
# → {"error": "foreign_campaign", "message": "Кампания 75000001 недоступна — принадлежит другому аккаунту"}

# Лимит API (слишком много ID за раз)
mcp__yandex_direct__ads_list(campaign_ids="1,2,3,4,5,6,7,8,9,10,11")
# → {"error": "batch_limit", "message": "Максимум 10 ID за запрос. Передано: 11"}

# direct-cli не установлен или не в PATH
mcp__yandex_direct__campaigns_list()
# → {"error": "cli_not_found", "message": "direct-cli не найден. Установите: https://github.com/axisrow/direct-cli"}

# Заявка на доступ к API не подана или отклонена (ошибка 58)
mcp__yandex_direct__campaigns_list()
# → {"error": "incomplete_registration", "message": "Незаконченная регистрация. Вам нужно подать или переподать заявку..."}
```

### Without plugin (before)

```bash
export BW_SESSION="$(bw unlock --raw)"
direct-cli --bw-token-ref "yandex-direct" --bw-login-ref "yandex-direct" \
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
| 1 | Обмен кода на токен | `auth_setup(code=...)` → POST `/token` | `{"success": True, "access_token", "refresh_token"}` |
| 2 | Неверный код | `auth_setup(code="0000000")` | `{"error": "invalid_grant"}` |
| 3 | Просроченный код (>10 мин) | `auth_setup(code=...)` после паузы | `{"error": "invalid_grant"}` |
| 4 | Автообновление токена | Запрос с истёкшим `access_token` | Refresh → новый токен → повтор запроса → успех |
| 5 | Refresh тоже протух | Оба токена невалидны | `{"error": "auth_expired", "auth_url"}` |
| 6 | Статус токена | `auth_status()` | `{"valid": True/False, "expires_in", "login"}` |
| **Campaigns** |
| 7 | Список всех кампаний | `campaigns_list()` | Массив кампаний с Id, Name, State |
| 8 | Фильтр по статусу | `campaigns_list(state="ON")` | Только кампании с State=ON |
| 9 | Включить кампанию | `campaigns_update(id=..., state="ON")` | `{"success": True}` |
| 10 | Несуществующая кампания | `campaigns_update(id="999")` | `{"error": "not_found"}` |
| **Ads** |
| 11 | Объявления в кампании | `ads_list(campaign_ids="12345")` | Массив объявлений |
| 12 | Кампания второго аккаунта | `ads_list(campaign_ids="75000001")` | `{"error": "foreign_campaign"}` |
| 13 | Превышение лимита ID | `ads_list(campaign_ids="1,2,...,11")` | `{"error": "batch_limit"}` |
| **Keywords** |
| 14 | Ключевые слова | `keywords_list(campaign_ids="12345")` | Массив ключевых слов |
| 15 | Изменить ставку | `keywords_update(id=..., bid=...)` | `{"success": True}` |
| **Reports** |
| 16 | Статистика за период | `reports_get(date_from=..., date_to=...)` | Массив с CampaignName, Impressions, Clicks, Cost, Conversions |
| **Edge cases** |
| 17 | direct-cli не в PATH | Запрос без установленного CLI | `{"error": "cli_not_found"}` |
| 18 | Пустой ответ API | Кампания без объявлений | `[]` (пустой массив, не ошибка) |
| 19 | Таймаут direct-cli | CLI зависает >30с | `{"error": "timeout"}` |

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
│   ├── ads.json             # Мок-данные объявлений
│   └── tokens.json          # Мок-токены
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
│  direct-cli ──→ Яндекс API ──→ сырые ответы                    │
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

`direct-cli` запускается как subprocess — HTTP-рекордеры (nock, polly, responses, vcrpy) работают только in-process и его запросы не перехватят. Поэтому записываем на уровне CLI:

```
┌──────────────┐            ┌──────────────┐         ┌──────────────┐
│  MCP Server  │──subprocess──▶│  direct-cli  │──HTTP──▶│  Яндекс API  │
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
1. **Режим записи** (`RECORD=true`): MCP-сервер вызывает реальный `direct-cli`, `cli_recorder.py` сохраняет пару `{args, stdout, stderr, returncode}` в JSON-файл
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
  "command": "direct-cli",
  "args": ["--token", "REDACTED", "campaigns", "get", "--format", "json"],
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
- `cli_not_found` — direct-cli не установлен (`FileNotFoundError`)
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
| `.env.test` создаётся автоматически | См. ниже |

### Setup for Recording

`.env.test` нужен **только для записи кассет** — обычный `pytest` работает без него.

```bash
# 1. Запустить скрипт настройки (интерактивно)
python -m tests.setup
```

Скрипт `tests.setup` делает:
1. Вызывает `mcp__yandex_direct__auth_status()` — если плагин уже авторизован, берёт токен оттуда
2. Если нет — открывает `https://oauth.yandex.ru/authorize?...` в браузере
3. Просит ввести 7-значный код
4. Обменивает код на токен
5. Записывает `.env.test` (в `.gitignore`, не попадёт в репо):

```env
# Auto-generated by python -m tests.setup — DO NOT COMMIT
YANDEX_OAUTH_TOKEN=AQAAAACy1C6ZAAAAfa6v...
YANDEX_CLIENT_ID=abc123
YANDEX_CLIENT_SECRET=secret456
YANDEX_LOGIN=ksamatadirect
```

6. Создаёт `.env.test.example` (коммитится, без секретов):

```env
# Copy to .env.test and fill in your values
YANDEX_OAUTH_TOKEN=
YANDEX_CLIENT_ID=
YANDEX_CLIENT_SECRET=
YANDEX_LOGIN=
```

Дальше `pytest --record` подхватывает `.env.test`, записывает кассеты и сразу прогоняет санитизацию.

**Итого: `pytest` не требует токенов. Токен нужен только для `--record`, и скрипт сам его получит.**

## Tech Stack

| Слой | Технология | Версия | Зачем |
|---|---|---|---|
| **Runtime** | Python | >= 3.11 | Единый язык с direct-cli |
| **MCP Server** | [mcp](https://pypi.org/project/mcp/) | latest | Python SDK для MCP (stdio transport) |
| **CLI** | [direct-cli](https://github.com/axisrow/direct-cli) | latest | Обёртка над Яндекс.Директ API |
| **HTTP** | [httpx](https://www.python-httpx.org/) | >= 0.27 | OAuth-запросы к `oauth.yandex.ru` |
| **Testing** | [pytest](https://docs.pytest.org/) | >= 8.0 | Тесты, fixtures, markers |
| **Mocking** | `unittest.mock` | stdlib | Моки subprocess для edge cases |
| **Cassettes** | `cli_recorder.py` (свой) | — | Запись/воспроизведение CLI stdin/stdout |
| **Config** | [python-dotenv](https://pypi.org/project/python-dotenv/) | >= 1.0 | Загрузка `.env.test` |
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
| Bitwarden | Заменён на встроенный OAuth-модуль |

### pyproject.toml

```toml
[project]
name = "yandex-direct-mcp-plugin"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "mcp",
    "httpx>=0.27",
    "python-dotenv>=1.0",
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
