---
name: yandex-direct
description: "Управление Яндекс.Директ через MCP tools. Активируй когда пользователь упоминает Яндекс.Директ, хочет управлять кампаниями, объявлениями, ключевыми словами, ставками, бюджетом, или получить статистику."
user-invocable: true
argument-hint: "[вопрос или команда по Яндекс.Директ]"
---

# Яндекс.Директ — управление через MCP tools

Управление рекламными кампаниями в Яндекс.Директ через MCP-инструменты плагина.

## Первое действие — проверь авторизацию

**Всегда начинай с `auth_status()`.** Если `valid: false`:
1. Вызови `auth_login()` — он покажет ссылку для авторизации и запросит код через форму
2. Пользователю не нужно ничего знать заранее — flow полностью интерактивный
3. После авторизации токен сохраняется на диск, повторный логин не требуется

Не пытайся вызывать другие tools пока авторизация не пройдена — они вернут ошибку.

## Доступные MCP Tools (105)

### Кампании
| Tool | Описание | Параметры |
|---|---|---|
| `campaigns_list` | Список кампаний | `state?` (ON/OFF) |
| `campaigns_update` | Изменить статус кампании | `id`, `state` (ON/OFF) |
| `campaigns_add` | Создать кампанию | `name`, `start_date` |
| `campaigns_delete` | Удалить кампании | `ids` (max 10) |
| `campaigns_archive` | Архивировать кампании | `ids` (max 10) |
| `campaigns_unarchive` | Разархивировать кампании | `ids` (max 10) |
| `campaigns_suspend` | Приостановить кампании | `ids` (max 10) |
| `campaigns_resume` | Возобновить кампании | `ids` (max 10) |

### Группы объявлений
| Tool | Описание | Параметры |
|---|---|---|
| `adgroups_list` | Список групп объявлений | `campaign_ids` (max 10) |
| `adgroups_add` | Создать группу | `campaign_id`, `name`, `region_ids` |
| `adgroups_update` | Обновить группу | `id`, `name` |
| `adgroups_delete` | Удалить группы | `ids` (max 10) |

### Объявления
| Tool | Описание | Параметры |
|---|---|---|
| `ads_list` | Список объявлений | `campaign_ids` (max 10) |
| `ads_add` | Создать объявление | `ad_group_id`, `title?`, `text?`, `href?` |
| `ads_update` | Обновить объявление | `id`, `extra_json?` |
| `ads_delete` | Удалить объявления | `ids` (max 10) |
| `ads_moderate` | Отправить на модерацию | `ids` (max 10) |
| `ads_suspend` | Приостановить объявления | `ids` (max 10) |
| `ads_resume` | Возобновить объявления | `ids` (max 10) |
| `ads_archive` | Архивировать объявления | `ids` (max 10) |
| `ads_unarchive` | Разархивировать объявления | `ids` (max 10) |

### Ключевые слова
| Tool | Описание | Параметры |
|---|---|---|
| `keywords_list` | Список ключевых слов | `campaign_ids` (max 10) |
| `keywords_update` | Изменить ставку | `id`, `bid` (micro-units) |
| `keywords_add` | Добавить ключевое слово | `ad_group_id`, `keyword`, `bid?` |
| `keywords_delete` | Удалить ключевые слова | `ids` (max 10) |
| `keywords_suspend` | Приостановить ключевые слова | `ids` (max 10) |
| `keywords_resume` | Возобновить ключевые слова | `ids` (max 10) |
| `keywords_archive` | Архивировать ключевые слова | `ids` (max 10) |
| `keywords_unarchive` | Разархивировать ключевые слова | `ids` (max 10) |

### Ставки на ключевые слова
| Tool | Описание | Параметры |
|---|---|---|
| `keyword_bids_list` | Список ставок на ключевые слова | `campaign_ids`, `ad_group_ids?`, `keyword_ids?` |
| `keyword_bids_set` | Установить ставку на ключевое слово | `keyword_id`, `bid?`, `context_bid?` |

### Ставки
| Tool | Описание | Параметры |
|---|---|---|
| `bids_list` | Список ставок | `campaign_ids` (max 10) |
| `bids_set` | Установить ставку | `campaign_id`, `bid`, `context_bid?` |

### Корректировки ставок
| Tool | Описание | Параметры |
|---|---|---|
| `bidmodifiers_list` | Список корректировок | `campaign_ids` (max 10) |
| `bidmodifiers_set` | Установить корректировку | `campaign_id`, `modifier_type`, `value` |
| `bidmodifiers_toggle` | Вкл/выкл корректировку | `id`, `enabled` |
| `bidmodifiers_delete` | Удалить корректировки | `ids` (max 10) |

### Расширения объявлений
| Tool | Описание | Параметры |
|---|---|---|
| `sitelinks_list` | Список наборов ссылок | `ids` (max 10) |
| `sitelinks_add` | Добавить набор ссылок | `sitelinks_data` (JSON) |
| `sitelinks_delete` | Удалить наборы ссылок | `ids` (max 10) |
| `vcards_list` | Список визиток | `ids` (max 10) |
| `vcards_add` | Добавить визитку | `vcard_data` (JSON) |
| `vcards_delete` | Удалить визитки | `ids` (max 10) |
| `adimages_list` | Список изображений | `ids` |
| `adimages_add` | Добавить изображение | `image_data` (base64) |
| `adimages_delete` | Удалить изображения | `ids` |
| `adextensions_list` | Список расширений | `ids` |
| `adextensions_add` | Добавить расширение | `extension_type`, `extension_data` (JSON) |
| `adextensions_delete` | Удалить расширения | `ids` |

### Таргетинг и аудитории
| Tool | Описание | Параметры |
|---|---|---|
| `audience_targets_list` | Список аудиторий | `campaign_ids` (max 10) |
| `audience_targets_add` | Добавить аудиториою | `campaign_id`, `ad_group_id`, `audience_id` |
| `audience_targets_delete` | Удалить аудитории | `ids` (max 10) |
| `audience_targets_suspend` | Приостановить аудитории | `ids` (max 10) |
| `audience_targets_resume` | Возобновить аудитории | `ids` (max 10) |
| `retargeting_list` | Список ретаргетингов | `ids` |
| `retargeting_add` | Добавить ретаргетинг | `name`, `rule` (JSON) |
| `retargeting_delete` | Удалить ретаргетинги | `ids` (max 10) |
| `dynamic_targets_list` | Список динамических таргетов | `ad_group_ids` (max 10) |
| `dynamic_targets_add` | Добавить динамический таргет | `ad_group_id`, `conditions` (JSON) |
| `dynamic_targets_update` | Обновить динамический таргет | `id`, `conditions` (JSON) |
| `dynamic_targets_delete` | Удалить динамические таргеты | `ids` (max 10) |
| `dynamic_ads_list` | Список динамических объявлений | `ad_group_ids` |
| `dynamic_ads_add` | Добавить динамическое объявление | `ad_group_id`, `target_data` (JSON) |
| `dynamic_ads_update` | Обновить динамическое объявление | `id`, `extra_json` (JSON) |
| `dynamic_ads_delete` | Удалить динамические объявления | `id` |
| `negative_keywords_list` | Список минус-слов | `campaign_ids` (max 10) |
| `negative_keywords_add` | Добавить минус-слова | `campaign_id`, `keywords` |
| `negative_keywords_update` | Обновить минус-слова | `id`, `keywords` |
| `negative_keywords_delete` | Удалить минус-слова | `ids` (max 10) |
| `smart_targets_list` | Список смарт-таргетов | `ad_group_ids` (max 10) |
| `smart_targets_add` | Добавить смарт-таргет | `ad_group_id`, `conditions` (JSON) |
| `smart_targets_update` | Обновить смарт-таргет | `id`, `conditions` (JSON) |
| `smart_targets_delete` | Удалить смарт-таргеты | `ids` (max 10) |
| `smart_ad_targets_list` | Список смарт-таргетов объявлений | `ad_group_ids` |
| `smart_ad_targets_add` | Добавить смарт-таргет объявлений | `ad_group_id`, `target_type`, `extra_json?` |
| `smart_ad_targets_update` | Обновить смарт-таргет объявлений | `id`, `extra_json` |
| `smart_ad_targets_delete` | Удалить смарт-таргет объявлений | `id` |
| `negative_keyword_shared_sets_list` | Список наборов минус-слов | `ids?` |
| `negative_keyword_shared_sets_add` | Добавить набор минус-слов | `name`, `keywords` |
| `negative_keyword_shared_sets_update` | Обновить набор минус-слов | `id`, `name?`, `keywords?` |
| `negative_keyword_shared_sets_delete` | Удалить набор минус-слов | `id` |
| `businesses_list` | Список бизнесов | `ids?` |

### Справочники и изменения
| Tool | Описание | Параметры |
|---|---|---|
| `dictionaries_get` | Получить справочник | `dictionary_type`, `locale?` |
| `changes_check` | Проверить изменения | `timestamp` |
| `changes_checkcamp` | Изменения по кампаниям | `campaign_ids`, `timestamp` |
| `changes_checkdict` | Изменения справочников | `timestamp` |

### Клиенты и агентство
| Tool | Описание | Параметры |
|---|---|---|
| `clients_get` | Информация о клиенте | `login?` |
| `clients_update` | Обновить клиента | `login`, `fields` (JSON) |
| `agency_clients_list` | Клиенты агентства | `login?` |
| `agency_clients_add` | Добавить клиента агентству | `login`, `client_info` (JSON) |
| `agency_clients_delete` | Удалить клиента из агентства | `login`, `client_login` |

### Исследования и отчёты
| Tool | Описание | Параметры |
|---|---|---|
| `keywords_has_volume` | Проверить объём по ключевым словам | `keywords`, `region_id?` |
| `keywords_deduplicate` | Дедупликация ключевых слов | `keywords` |
| `leads_list` | Список лидов | `campaign_ids`, `date_from?`, `date_to?` |
| `reports_get` | Статистика кампаний | `date_from?`, `date_to?` |
| `reports_list_types` | Список типов отчётов | — |

### Фиды, креативы, Турбо-страницы
| Tool | Описание | Параметры |
|---|---|---|
| `feeds_list` | Список фидов | `ids` |
| `feeds_add` | Добавить фид | `name`, `url` |
| `feeds_update` | Обновить фид | `id`, `name?`, `url?` |
| `feeds_delete` | Удалить фиды | `ids` (max 10) |
| `creatives_list` | Список креативов | `ids` |
| `turbo_pages_list` | Список Турбо-страниц | `ids` |

### Авторизация
| Tool | Описание | Параметры |
|---|---|---|
| `auth_status` | Статус OAuth-токена | — |
| `auth_setup` | Ввести код авторизации | `code` (7 digits или y0_ токен) |
| `auth_login` | Интерактивный OAuth (браузер + ввод кода) | — |

## Типичные запросы

| Запрос пользователя | MCP Tool |
|---|---|
| Покажи все кампании | `campaigns_list()` |
| Покажи активные кампании | `campaigns_list(state="ON")` |
| Создай кампанию | `campaigns_add(name="...", start_date="2024-01-01")` |
| Сколько объявлений в кампании 123? | `ads_list(campaign_ids="123")` → count |
| Включи кампанию 456 | `campaigns_update(id="456", state="ON")` |
| Отключи кампанию 456 | `campaigns_update(id="456", state="OFF")` |
| Ключевые слова кампании 789 | `keywords_list(campaign_ids="789")` |
| Изменить ставку ключевого слова на 15 руб | `keywords_update(id="99999", bid="15000000")` |
| Статистика за последнюю неделю | `reports_get(date_from="...", date_to="...")` |
| Установить ставку 10 руб на кампанию | `bids_set(campaign_id="123", bid="10000000")` |
| Проверить есть ли изменения в кампаниях | `changes_checkcamp(campaign_ids="123", timestamp="...")` |
| Показать группы объявлений | `adgroups_list(campaign_ids="123")` |
| Токен живой? | `auth_status()` |

## Важные детали

### Микроюниты для ставок
Ставки передаются в микроюнитах: **15 RUB = 15,000,000**. Всегда умножайте рубли на 1,000,000.

### API-лимиты и батчинг
- Максимум **10 ID** за запрос для list/delete операций
- Для больших наборов делайте несколько запросов по 5-10 ID

### Второй аккаунт
- Кампании с ID в диапазоне **73M-77M** принадлежат второму аккаунту
- Запросы к ним вернут ошибку `foreign_campaign`
- Эти кампании недоступны через текущий логин

### Статусы кампаний
- `ON` — активная кампания
- `OFF` — приостановлена
- `ARCHIVED` — в архиве

### Авторизация
- Для интерактивной авторизации используйте `auth_login()` — покажет ссылку и запросит код
- Для ручной авторизации: `auth_setup(code="...")` с кодом авторизации или `auth_setup(code="y0_...")` с готовым токеном
- Токен сохраняется на диск и автоматически обновляется через refresh_token
- Если refresh_token тоже протух, пользователь получит URL для повторной авторизации

### Запуск Python-скриптов

В zsh/bash символ `!` в heredoc (`<< 'EOF'`) интерпретируется как history expansion. Операторы `!=` в Python-коде превращаются в `\!=` → `SyntaxError`. Всегда записывайте Python-скрипт в файл через `Write`, затем запускайте через `python3 /path/to/script.py`.
