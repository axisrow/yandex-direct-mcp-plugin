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

## Доступный MCP-контракт (124 tools)

Контракт теперь следует иерархии:

`MCP -> direct-cli -> tapi-yandex-direct -> Yandex.Direct API`

- Используй только публичные MCP tools.
- Не опирайся на старые alias-имена (`*_list`, `agency_clients_*`, `keyword_bids_*`, `smart_targets_*` и т.д.).
- Для Direct-операций используй канонические имена `service_method`.
- v4 Live методы вызывай только через публичные MCP tools; shell-группы без CLI-команд не используются.

### Правила именования

- `*_list` → `*_get`: `campaigns_get`, `ads_get`, `keywords_get`
- Имена сервисов совпадают с `direct-cli`: `agencyclients_*`, `audiencetargets_*`, `keywordbids_*`, `smartadtargets_*`, `dynamicads_*`, `negativekeywordsharedsets_*`, `turbopages_get`
- CLI методы с дефисом становятся snake_case:
  - `changes_check_campaigns`
  - `changes_check_dictionaries`
  - `keywordsresearch_has_search_volume`
  - `bids_set_auto`
  - `keywordbids_set_auto`
  - `audiencetargets_set_bids`
  - `dynamicads_set_bids`
  - `smartadtargets_set_bids`

### Direct API tools — основные семейства

| Семейство | Канонические tools |
|---|---|
| Кампании | `campaigns_get/add/update/delete/archive/unarchive/suspend/resume` |
| Группы / объявления / ключи | `adgroups_get/add/update/delete`, `ads_get/add/update/delete/moderate/suspend/resume/archive/unarchive`, `keywords_get/add/update/delete/suspend/resume/archive/unarchive` |
| Ставки | `keywordbids_get/set/set_auto`, `bids_get/set/set_auto`, `bidmodifiers_get/add/set/delete` |
| Таргетинг | `audiencetargets_get/add/delete/suspend/resume/set_bids`, `retargeting_get/add/update/delete`, `dynamicads_get/add/delete/suspend/resume/set_bids`, `dynamicfeedadtargets_get/add/delete/suspend/resume/set_bids`, `smartadtargets_get/add/update/delete/suspend/resume/set_bids` |
| Стратегии | `strategies_get/add/update/archive/unarchive` |
| Медиа и расширения | `adimages_get/add/delete`, `advideos_get/add`, `adextensions_get/add/delete`, `sitelinks_get/add/delete`, `vcards_get/add/delete`, `creatives_get/add` |
| Справочники / изменения / отчёты | `dictionaries_get`, `dictionaries_get_geo_regions`, `changes_check`, `changes_check_campaigns`, `changes_check_dictionaries`, `reports_get` |
| v4 Live | `balance_get`, `v4goals_get_stat_goals`, `v4goals_get_retargeting_goals` |
| Прочее | `clients_get/update`, `agencyclients_get/add/update/add_passport_organization/add_passport_organization_member`, `businesses_get`, `feeds_get/add/update/delete`, `leads_get`, `negativekeywordsharedsets_get/add/update/delete`, `keywordsresearch_has_search_volume`, `keywordsresearch_deduplicate`, `turbopages_get` |

### Явно helper-only tools

Эти tools публичные, но не являются 1:1 Direct API методами:

- `agencyclients_delete`
- `dictionaries_list_names`
- `reports_list_types`

### Plugin-only auth tools

- `auth_status`
- `auth_setup`
- `auth_login`

## Типичные запросы

| Запрос пользователя | MCP Tool |
|---|---|
| Покажи все кампании | `campaigns_get()` |
| Покажи активные кампании | `campaigns_get(state="ON")` |
| Создай кампанию | `campaigns_add(name="...", start_date="2024-01-01")` |
| Сколько объявлений в кампании 123? | `ads_get(campaign_ids="123")` → count |
| Включи кампанию 456 | `campaigns_update(id=456, status="ON")` |
| Отключи кампанию 456 | `campaigns_update(id=456, status="OFF")` |
| Ключевые слова кампании 789 | `keywords_get(campaign_ids="789")` |
| Изменить ставку ключевого слова на 15 руб | `keyword_bids_set(keyword_id=99999, search_bid=15000000)` |
| Установить дневной бюджет 500 руб | `campaigns_update(id=456, budget=500000000)` |
| Установить ставку 10 руб на кампанию | `bids_set(campaign_id=123, bid=10000000)` |
| Ставка показа на dynamic-target | `dynamic_ads_set_bids(id=42, bid=5000000)` |
| Средняя CPC для smart-таргета | `smart_ad_targets_set_bids(id=42, average_cpc=8000000)` |
| Статистика за последнюю неделю | `reports_get(date_from="...", date_to="...")` |
| Баланс аккаунта | `balance_get()` |
| Цели Метрики для кампаний | `v4goals_get_stat_goals(campaign_ids="123")` |
| Ретаргетинговые цели для кампаний | `v4goals_get_retargeting_goals(campaign_ids="123")` |
| Проверить есть ли изменения в кампаниях | `changes_check_campaigns(campaign_ids="123", timestamp="...")` |
| Показать группы объявлений | `adgroups_get(campaign_ids="123")` |
| Токен живой? | `auth_status()` |

## Важные детали

### Микроюниты для ставок
Все money-параметры (ставки, бюджеты, CPC/CPA, потолки) передаются в **микрорублях**:
**15 RUB = 15,000,000**. Умножайте рубли на 1,000,000.

CLI 0.2.10+ отвергает значения в диапазоне `0 < x < 100_000` (меньше 0.1 ₽) с подсказкой
«did you mean × 1_000_000?» — обычная защита от того, что вы случайно передали рубли вместо микрорублей.

Все идентификаторы (`id`, `campaign_id`, `ad_group_id`, `keyword_id`, `client_id`, `region_id` и т.д.)
и money-параметры — целые числа (`int`), а **не строки**. Списки идентификаторов через запятую
(`*_ids`) — наоборот, передаются строкой `"1,2,3"`.

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
