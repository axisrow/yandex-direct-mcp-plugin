# yandex-direct-mcp-plugin

Claude Code plugin for managing Yandex.Direct advertising campaigns.

## Features

- **MCP Server** — structured tools for campaigns, ads, keywords, and reports
- **Skills** — domain knowledge for Yandex.Direct management and ad copywriting
- **OAuth 2.0** — automatic token management with refresh support (no Bitwarden dependency)

## Architecture

```
direct-cli (CLI)        — низкоуровневая утилита, общается с Яндекс.Директ API
       ↑
MCP Server (MCP)        — обёртка над CLI, выставляет структурированные инструменты
       ↑
Skill (SKILL.md)        — доменные знания: когда какой инструмент вызвать, лимиты, подводные камни
       ↑
Plugin (.claude-plugin) — контейнер, объединяющий MCP + скиллы + OAuth в единый пакет
```

| Компонент | Что это | Что делает | Без него |
|---|---|---|---|
| **direct-cli** | CLI-утилита | Выполняет запросы к Яндекс.Директ API | Ничего не работает |
| **MCP Server** | Процесс (stdio) | Превращает CLI в структурированные инструменты с типизированными параметрами и ответами | Claude собирает bash-команды вручную |
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

## Setup

On first use, the plugin will ask for:
- **client_id** — your Yandex OAuth application ID
- **client_secret** — your Yandex OAuth application secret

Then authorize via:
```
mcp__yandex_direct__auth_setup(code="<7-digit code>")
```

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
| `auth_setup` | Submit authorization code |

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

```javascript
// Список активных кампаний
mcp__yandex_direct__campaigns_list({ state: "ON" })
// → [{ Id: 12345, Name: "Кампания 1", State: "ON", DailyBudget: 5000 }, ...]

// Объявления в кампании
mcp__yandex_direct__ads_list({ campaign_ids: "12345" })
// → [{ Id: 111, Title: "Доставка пиццы", Title2: "За 30 минут", State: "ON" }, ...]

// Включить/отключить кампанию
mcp__yandex_direct__campaigns_update({ id: "67890", state: "OFF" })
// → { success: true, id: 67890, state: "OFF" }

// Ключевые слова
mcp__yandex_direct__keywords_list({ campaign_ids: "12345" })
// → [{ Id: 99999, Keyword: "пицца доставка", Bid: 12000000 }, ...]

// Изменить ставку (в микроюнитах: 15 руб = 15000000)
mcp__yandex_direct__keywords_update({ id: "99999", bid: "15000000" })
// → { success: true, id: 99999, bid: 15000000 }

// Статистика
mcp__yandex_direct__reports_get({ date_from: "2026-03-30", date_to: "2026-04-06" })
// → [{ CampaignId: 12345, Impressions: 15420, Clicks: 312, Cost: 4680.50 }, ...]

// Статус OAuth-токена
mcp__yandex_direct__auth_status()
// → { valid: true, expires_in: 7200, scope: "direct:...", login: "ksamatadirect" }

// Авторизация (первый раз)
mcp__yandex_direct__auth_setup({ code: "1234567" })
// → { success: true, access_token: "AQA...", expires_in: 124234123534 }
```

### Error Handling

```javascript
// Токен истёк → MCP-сервер обновит автоматически через refresh_token
mcp__yandex_direct__campaigns_list({ state: "ON" })
// 1) access_token expired → POST /token { grant_type: "refresh_token" }
// 2) новый access_token сохранён → повторный запрос → результат

// Токен невалиден (refresh тоже протух)
mcp__yandex_direct__campaigns_list({ state: "ON" })
// → { error: "auth_expired", message: "Требуется повторная авторизация",
//    auth_url: "https://oauth.yandex.ru/authorize?client_id=..." }

// Неверный код авторизации
mcp__yandex_direct__auth_setup({ code: "0000000" })
// → { error: "invalid_grant", message: "Неверный или просроченный код. Код действует 10 минут." }

// Кампания не найдена
mcp__yandex_direct__campaigns_update({ id: "999", state: "ON" })
// → { error: "not_found", message: "Кампания 999 не найдена в аккаунте ksamatadirect" }

// Кампания принадлежит второму аккаунту (ID ~73-77М)
mcp__yandex_direct__ads_list({ campaign_ids: "75000001" })
// → { error: "foreign_campaign", message: "Кампания 75000001 недоступна — принадлежит другому аккаунту" }

// Лимит API (слишком много ID за раз)
mcp__yandex_direct__ads_list({ campaign_ids: "1,2,3,4,5,6,7,8,9,10,11" })
// → { error: "batch_limit", message: "Максимум 10 ID за запрос. Передано: 11" }

// direct-cli не установлен или не в PATH
mcp__yandex_direct__campaigns_list({})
// → { error: "cli_not_found", message: "direct-cli не найден. Установите: https://github.com/axisrow/direct-cli" }
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
npm test
```

### Test Coverage

| # | Сценарий | Что проверяем | Ожидаемый результат |
|---|---|---|---|
| **Auth** |
| 1 | Обмен кода на токен | `auth_setup({ code })` → POST `/token` | `{ success: true, access_token, refresh_token }` |
| 2 | Неверный код | `auth_setup({ code: "0000000" })` | `{ error: "invalid_grant" }` |
| 3 | Просроченный код (>10 мин) | `auth_setup({ code })` после паузы | `{ error: "invalid_grant" }` |
| 4 | Автообновление токена | Запрос с истёкшим `access_token` | Refresh → новый токен → повтор запроса → успех |
| 5 | Refresh тоже протух | Оба токена невалидны | `{ error: "auth_expired", auth_url }` |
| 6 | Статус токена | `auth_status()` | `{ valid: true/false, expires_in, login }` |
| **Campaigns** |
| 7 | Список всех кампаний | `campaigns_list({})` | Массив кампаний с Id, Name, State |
| 8 | Фильтр по статусу | `campaigns_list({ state: "ON" })` | Только кампании с State=ON |
| 9 | Включить кампанию | `campaigns_update({ id, state: "ON" })` | `{ success: true }` |
| 10 | Несуществующая кампания | `campaigns_update({ id: "999" })` | `{ error: "not_found" }` |
| **Ads** |
| 11 | Объявления в кампании | `ads_list({ campaign_ids: "12345" })` | Массив объявлений |
| 12 | Кампания второго аккаунта | `ads_list({ campaign_ids: "75000001" })` | `{ error: "foreign_campaign" }` |
| 13 | Превышение лимита ID | `ads_list({ campaign_ids: "1,2,...,11" })` | `{ error: "batch_limit" }` |
| **Keywords** |
| 14 | Ключевые слова | `keywords_list({ campaign_ids: "12345" })` | Массив ключевых слов |
| 15 | Изменить ставку | `keywords_update({ id, bid })` | `{ success: true }` |
| **Reports** |
| 16 | Статистика за период | `reports_get({ date_from, date_to })` | Массив с Impressions, Clicks, Cost |
| **Edge cases** |
| 17 | direct-cli не в PATH | Запрос без установленного CLI | `{ error: "cli_not_found" }` |
| 18 | Пустой ответ API | Кампания без объявлений | `[]` (пустой массив, не ошибка) |
| 19 | Таймаут direct-cli | CLI зависает >30с | `{ error: "timeout" }` |

### Test Structure

```
server/
├── __tests__/
│   ├── auth.test.js          # Тесты 1-6: OAuth flow
│   ├── campaigns.test.js     # Тесты 7-10: кампании
│   ├── ads.test.js           # Тесты 11-13: объявления
│   ├── keywords.test.js      # Тесты 14-15: ключевые слова
│   ├── reports.test.js       # Тест 16: отчёты
│   ├── edge-cases.test.js    # Тесты 17-19: граничные случаи
│   └── fixtures/
│       ├── campaigns.json    # Мок-данные кампаний
│       ├── ads.json          # Мок-данные объявлений
│       └── tokens.json       # Мок-токены
```

### Test Modes

**1. Cassettes (recorded API responses)** — основной режим

```bash
# Записать кассеты с реального API (один раз)
npm run test:record

# Прогнать тесты на записанных кассетах (CI/повседневно)
npm test
```

Кассеты записываются через [nock](https://github.com/nock/nock) `recorder` или [polly.js](https://netflix.github.io/pollyjs/):
- Первый прогон идёт в реальный API и сохраняет HTTP-ответы в `__recordings__/`
- Последующие прогоны воспроизводят записи без сети
- Токены и секреты автоматически маскируются при записи

```
server/
├── __tests__/
│   ├── __recordings__/            # Записанные кассеты
│   │   ├── auth/
│   │   │   ├── token-exchange.json
│   │   │   ├── token-refresh.json
│   │   │   └── invalid-code.json
│   │   ├── campaigns/
│   │   │   ├── list-all.json
│   │   │   ├── list-active.json
│   │   │   └── update-state.json
│   │   ├── ads/
│   │   │   ├── list-by-campaign.json
│   │   │   └── foreign-campaign.json
│   │   ├── keywords/
│   │   │   └── list-and-update.json
│   │   └── reports/
│   │       └── weekly-stats.json
```

**2. Mocks** — для edge cases, которые нельзя записать

```bash
npm run test:mocks
```

Моки через `jest.mock('child_process')` только для сценариев, которых невозможно добиться от реального API:
- `cli_not_found` — direct-cli не установлен
- `timeout` — CLI зависает >30с
- `batch_limit` — валидация на стороне MCP-сервера, до вызова API

**3. Integration (live API)** — перед релизом

```bash
# Требует валидный OAuth-токен
npm run test:integration
```

Полный прогон через реальный API Яндекс.Директ. Используется для:
- Верификации кассет (не устарели ли?)
- Обновления записей: `npm run test:record`
- Smoke-тестов перед новой версией

### Cassette Recording Rules

| Правило | Почему |
|---|---|
| Кассеты коммитятся в git | Тесты работают без API-ключей |
| Секреты маскируются (`access_token` → `REDACTED`) | Безопасность |
| Кассеты перезаписываются перед мажорным релизом | Актуальность |
| Edge cases остаются моками | Невоспроизводимы через API |
| `.env.test` с тестовым OAuth-токеном в `.gitignore` | Не утечёт в репо |

## Requirements

- [direct-cli](https://github.com/axisrow/direct-cli) installed and in PATH
- Node.js >= 18
- Yandex OAuth application registered at https://oauth.yandex.ru/

## License

MIT
