---
name: yandex-direct-cli
description: "Управление Яндекс.Директ через direct-cli с аутентификацией Bitwarden (legacy). Используй только если нужна работа через CLI напрямую, а не через MCP-плагин."
user-invocable: true
argument-hint: "[вопрос или команда по Яндекс.Директ, например: 'покажи активные кампании', 'сколько объявлений', 'включи кампанию ID']"
---

# Яндекс.Директ через direct-cli

Управление рекламными кампаниями в Яндекс.Директ через CLI с аутентификацией через Bitwarden.

## Шаг 1: Проверка и инициализация Bitwarden сессии

Перед выполнением команд direct-cli нужно убедиться, что Bitwarden разблокирован и переменная окружения `BW_SESSION` установлена.

### Команды для проверки статуса

```bash
# Проверить статус Bitwarden
bw status

# Если сессия заблокирована, разблокировать (пароль нужен):
# echo '<пароль>' | bw unlock --raw
```

**Важно:** Переменная `BW_SESSION` должна быть в окружении текущей сессии оболочки. Если она не установлена, Bitwarden будет запрашивать пароль при каждой команде.

### Установка BW_SESSION (если нужна)

```bash
# Получить токен сессии и экспортировать в окружение
export BW_SESSION="$(bw unlock --raw --passwordfile <(echo 'password_here'))"
```

## Шаг 2: Структура команд direct-cli

Общий формат команды с Bitwarden-аутентификацией:

```bash
export BW_SESSION="<session_token>"
direct-cli \
  --bw-token-ref "yandex-direct" \
  --bw-login-ref "yandex-direct" \
  <подкоманда> [аргументы]
```

**Параметры:**
- `--bw-token-ref "yandex-direct"` — ссылка на токен в Bitwarden (поле type=login)
- `--bw-login-ref "yandex-direct"` — ссылка на логин в Bitwarden

**Клиент по умолчанию:** `ksamatadirect`

## Шаг 3: Частые команды по задачам

### Просмотр информации

#### Список всех кампаний
```bash
direct-cli --bw-token-ref "yandex-direct" --bw-login-ref "yandex-direct" \
  campaigns get --format table
```

#### Только активные кампании (State=ON)
```bash
direct-cli --bw-token-ref "yandex-direct" --bw-login-ref "yandex-direct" \
  campaigns get --format json | jq '.[] | select(.State == "ON")'
```

#### Объявления в кампании
```bash
direct-cli --bw-token-ref "yandex-direct" --bw-login-ref "yandex-direct" \
  ads get --campaign-ids <ID_кампании> --format table
```

#### Ключевые слова в кампании
```bash
direct-cli --bw-token-ref "yandex-direct" --bw-login-ref "yandex-direct" \
  keywords get --campaign-ids <ID_кампании> --format table
```

#### Статистика (отчёты)
```bash
direct-cli --bw-token-ref "yandex-direct" --bw-login-ref "yandex-direct" \
  reports get --format json
```

### Модификация

#### Изменить статус кампании (ON/OFF)
```bash
direct-cli --bw-token-ref "yandex-direct" --bw-login-ref "yandex-direct" \
  campaigns update --id <ID> --state ON
```

#### Изменить ставку ключевого слова
```bash
direct-cli --bw-token-ref "yandex-direct" --bw-login-ref "yandex-direct" \
  keywords update --id <ID> --bid <новая_ставка>
```

## Шаг 4: Батчинг (обработка нескольких кампаний)

API Яндекс.Директа ограничивает максимум 5-10 ID в одном запросе. Для получения объявлений по всем кампаниям используй батчинг:

```bash
# Получить все кампании
campaigns=$(direct-cli --bw-token-ref "yandex-direct" --bw-login-ref "yandex-direct" \
  campaigns get --format json | jq -r '.[].Id')

# Обработать пакетами по 5
for batch in $(echo "$campaigns" | paste -sd',' -); do
  direct-cli --bw-token-ref "yandex-direct" --bw-login-ref "yandex-direct" \
    ads get --campaign-ids "$batch" --format json
done
```

## Шаг 5: Обработка ошибок и проверка

### Проверить корректность аутентификации
```bash
direct-cli --bw-token-ref "yandex-direct" --bw-login-ref "yandex-direct" \
  campaigns get --format json | head
```

Если вернулось `401` или `Unauthorized` — проверь:
1. Установлена ли переменная `BW_SESSION`?
2. Существует ли элемент `yandex-direct` в Bitwarden?
3. Содержит ли элемент верный токен и логин?

### Проверить синтаксис команды
```bash
direct-cli help
direct-cli campaigns help
direct-cli ads help
```

## Шаг 6: Типичные сценарии использования

| Запрос пользователя | Команда |
|---|---|
| Покажи все кампании | `campaigns get --format table` |
| Покажи активные кампании | `campaigns get --format json \| jq '.[] \| select(.State == "ON")'` |
| Сколько объявлений в кампании 123? | `ads get --campaign-ids 123 --format json \| jq 'length'` |
| Сколько всего объявлений (батч) | см. Шаг 4 + `wc -l` |
| Включи кампанию 456 | `campaigns update --id 456 --state ON` |
| Отключи кампанию 456 | `campaigns update --id 456 --state OFF` |
| Покажи ключевые слова кампании 789 | `keywords get --campaign-ids 789 --format table` |
| Изменить ставку ключевого слова | `keywords update --id <ID> --bid <число>` |

## Шаг 7: Вывод результатов

Результаты можно форматировать:

- `--format table` — читаемая таблица
- `--format json` — JSON для программной обработки (pipe в `jq`)
- `--format csv` — CSV-формат (если поддерживается)

Используй таблицы для пользователя, JSON для батчинга и фильтрации.

## Важные детали

- **Требуемые параметры** для `ads get`: минимум один из `--ids`, `--campaign-ids`, `--adgroup-ids`
- **State=ON** означает активная кампания, **OFF** или **ARCHIVED** — неактивная
- **Логин по умолчанию:** `ksamatadirect` (клиент)
- **API-лимиты:** до 5-10 ID за раз для списков, батчинг обязателен для больших наборов
- **Токен Bitwarden** в элементе `yandex-direct` должен быть актуальный OAuth-токен Яндекса
- **Второй аккаунт:** часть кампаний (ID в диапазоне ~73-77М) принадлежит второму аккаунту Директа — `campaigns get` их не возвращает, `adgroups get` возвращает `[]`. Данные по ним доступны только через UTM-метки в regs/orders.

## Запуск Python-скриптов совместно с direct-cli

**Проблема с heredoc и `!`:** в zsh/bash символ `!` в heredoc (`<< 'EOF'`) интерпретируется как history expansion. Операторы `!=` в Python-коде превращаются в `\!=` → `SyntaxError`.

**Решение:** всегда записывать Python-скрипт в файл через `Write`, затем запускать через `python3 /path/to/script.py`:

```bash
# Неправильно — упадёт на != в Python-коде:
python3 << 'EOF'
df[df["col"] != "value"]
EOF

# Правильно — записать в файл и запустить:
# Write → /tmp/claude/script.py
python3 /tmp/claude/script.py
```
