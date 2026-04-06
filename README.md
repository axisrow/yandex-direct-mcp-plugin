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

## Requirements

- [direct-cli](https://github.com/axisrow/direct-cli) installed and in PATH
- Node.js >= 18
- Yandex OAuth application registered at https://oauth.yandex.ru/

## License

MIT
