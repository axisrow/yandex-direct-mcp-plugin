# План: Плагин yandex-direct с MCP-сервером и OAuth

## Context

Сейчас управление Яндекс.Директ реализовано как отдельный скилл (`SKILL.md`), который учит Claude вызывать `direct` через Bash. Аутентификация — через Bitwarden (токен хранится вручную). Это работает, но:
- Каждый вызов — сборка bash-команды вручную
- Токен может протухнуть, и нет автоматического обновления
- Нет структурированных ответов
- Сложно поделиться с другими

**Цель:** Превратить это в полноценный плагин Claude Code, который:
1. Содержит MCP-сервер (обёртка над `direct`, установленным пакетом `direct-cli`) — структурированные инструменты
2. Содержит скиллы (доменные знания) — yandex-direct + direct-ads
3. Встроенный OAuth-модуль — автоматическое получение и обновление токенов Яндекса

## Структура плагина

```
yandex-direct-plugin/
├── .claude-plugin/
│   └── plugin.json                 # Манифест
├── skills/
│   └── yandex-direct/
│       └── SKILL.md                # Доменные знания (адаптированный текущий скилл)
│   └── direct-ads/
│       └── SKILL.md                # Написание объявлений (скопировать существующий)
├── server/
│   ├── index.js                    # MCP-сервер (точка входа)
│   ├── tools/                      # Инструменты MCP
│   │   ├── campaigns.js            # campaigns.get, campaigns.update
│   │   ├── ads.js                  # ads.get
│   │   ├── keywords.js             # keywords.get, keywords.update
│   │   └── reports.js              # reports.get
│   ├── auth/
│   │   └── yandex-oauth.js         # OAuth 2.0 модуль
│   └── package.json
├── bin/
│   └── yandex-oauth-setup          # CLI для первоначальной авторизации
└── README.md
```

## Шаг 1: Инициализация плагина

Создать структуру директорий и `plugin.json`:

```json
{
  "name": "yandex-direct",
  "version": "0.1.5",
  "description": "Управление Яндекс.Директ: кампании, объявления, ставки, OAuth",
  "author": {"name": "axisrow"},
  "keywords": ["yandex", "direct", "advertising", "oauth"],
  "mcpServers": {
    "yandex-direct": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/server/index.js"],
      "env": {}
    }
  },
  "userConfig": {
    "client_id": {
      "description": "Client ID приложения Яндекс OAuth"
    },
    "client_secret": {
      "description": "Client Secret приложения Яндекс OAuth",
      "sensitive": true
    }
  }
}
```

## Шаг 2: Авторизация через direct-cli

Плагин не реализует собственный OAuth flow. Авторизация делегирована
`direct-cli`, который хранит token + login в `~/.direct-cli/auth.json`.

### Первоначальная авторизация
1. Запустить `direct auth login`
2. Пользователь подтверждает доступ, получает код
3. CLI обменивает код на токены и сохраняет профиль

### Автообновление
Refresh выполняет `direct` при использовании активного профиля `direct-cli`.

### API эндпоинты Яндекс OAuth (из документации)

- **Authorize:** `GET https://oauth.yandex.ru/authorize`
  - Параметры: `response_type=code`, `client_id`, `redirect_uri`, `scope`, `force_confirm`, `state`
  - Поддержка PKCE: `code_challenge`, `code_challenge_method=S256`
- **Token exchange:** `POST https://oauth.yandex.ru/token`
  - `grant_type=authorization_code` + `code` + `client_id` + `client_secret`
  - Или Basic Auth: `Authorization: Basic base64(client_id:client_secret)`
  - Ответ: `{ access_token, expires_in, token_type, refresh_token, scope }`
- **Refresh:** тот же endpoint, `grant_type=refresh_token` + `refresh_token`
- **Ошибки:** `invalid_grant`, `invalid_client`, `unauthorized_client`, `invalid_request`

## Шаг 3: MCP-сервер (`server/index.js`)

Node.js MCP-сервер (stdio transport) с инструментами:

| Инструмент | Параметры | Описание |
|---|---|---|
| `campaigns_list` | `state?`, `format?` | Список кампаний (фильтр по статусу) |
| `campaigns_update` | `id`, `state` | Вкл/выкл кампании |
| `ads_list` | `campaign_ids`, `format?` | Объявления в кампании |
| `keywords_list` | `campaign_ids`, `format?` | Ключевые слова |
| `keywords_update` | `id`, `bid` | Изменить ставку |
| `reports_get` | `date_from?`, `date_to?` | Статистика |
| `auth_status` | — | Статус OAuth-токена |
| `auth_setup` | `code` | Ввести код авторизации |

Сервер вызывает `direct` как subprocess, но:
- Передаёт OAuth-токен напрямую (не через Bitwarden)
- Парсит JSON-вывод и возвращает структурированно
- Автоматически обновляет токен при 401

## Шаг 4: Скиллы

### `skills/yandex-direct/SKILL.md`
Адаптировать текущий скилл — убрать инструкции по Bash/Bitwarden, добавить:
- Ссылки на MCP-инструменты вместо bash-команд
- Доменные знания (второй аккаунт, лимиты API, батчинг)
- Таблицу маппинга "запрос пользователя → MCP-инструмент"

### `skills/direct-ads/SKILL.md`
Скопировать существующий скилл написания объявлений из `~/.claude/skills/direct-ads/`.

## Шаг 5: Скрипт первоначальной настройки (`bin/yandex-oauth-setup`)

Bash-скрипт, который:
1. Запускает `direct auth login`
2. Делегирует CLI показ URL, ввод кода и сохранение профиля

## Верификация

1. `claude --plugin-dir ./yandex-direct-plugin` — запустить с плагином
2. `/yandex-direct:yandex-direct` — проверить скилл загружается
3. `mcp__yandex_direct__campaigns_list` — проверить MCP-инструмент работает
4. `mcp__yandex_direct__auth_status` — проверить OAuth-статус
5. Проверить автообновление: дождаться истечения токена → следующий вызов должен обновить автоматически

## Ключевые файлы

- `/Users/axisrow/.claude/skills/yandex-direct/SKILL.md` — текущий скилл (читать, адаптировать)
- `~/.claude/skills/direct-ads/SKILL.md` — скилл объявлений (скопировать)
- Всё остальное — новые файлы в новой директории плагина
