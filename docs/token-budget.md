# MCP tool-spec token budget — baseline

> Эпик [#149](https://github.com/axisrow/yandex-direct-mcp-plugin/issues/149),
> этап 1 («baseline и исследование»). Этот файл — зафиксированная точка отсчёта
> для последующих оптимизаций token budget. Любое сокращение поверхности или
> описаний должно иметь before/after против этих цифр.

## Что измеряется

Постоянная стоимость, которую плагин платит **в каждом запросе**, пока MCP-сервер
подключён: для каждого инструмента в `tools/list` — `name` + `description` +
`inputSchema` (JSON Schema параметров). Это то, что реально уходит в контекст
модели при инициализации MCP, независимо от того, вызывается инструмент или нет.

## Как воспроизвести

```bash
pip install -e ".[dev]"
pip install tiktoken          # опционально: точная оценка cl100k_base
python -m tests.measure_tool_tokens          # сводка + топ-20
python -m tests.measure_tool_tokens --json   # полный JSON по всем тулам
```

Без `tiktoken` скрипт падает на приближение `len/4` и явно помечает способ оценки
в выводе, чтобы цифры оставались сопоставимыми между запусками.

## Окружение замера

| Параметр | Значение |
|---|---|
| Дата | 2026-06-03 |
| Версия плагина | 0.3.0 |
| direct-cli (floor / установлен) | 0.4.2 / 0.4.2 |
| Способ оценки | tiktoken / cl100k_base (±~10% от токенайзера Claude) |
| Команда | `python -m tests.measure_tool_tokens` |

## Сводка

| Метрика | Значение |
|---|---:|
| Инструментов | 146 |
| **Суммарно токенов (спецификация)** | **40 792** |
| из них descriptions | 4 522 (11%) |
| из них JSON Schema параметров | 34 549 (85%) |
| Среднее на инструмент | 279 |

> Примечание: descriptions уже сжаты в 0.3.0 (progressive disclosure,
> PR #155: 16 582 → 4 522 токена, −73%). Основной остаточный вес теперь —
> **JSON Schema параметров** (85% бюджета), и он сконцентрирован в `campaigns_*`.

## Top-20 «тяжеловесов»

| # | tool | params | desc | schema | TOTAL |
|--:|---|--:|--:|--:|--:|
| 1 | `campaigns_update` | 219 | 42 | 6374 | **6427** |
| 2 | `campaigns_add` | 208 | 43 | 6067 | **6121** |
| 3 | `ads_update` | 43 | 42 | 1092 | 1144 |
| 4 | `ads_add` | 39 | 43 | 994 | 1047 |
| 5 | `clients_update` | 31 | 27 | 916 | 953 |
| 6 | `adgroups_update` | 27 | 41 | 767 | 819 |
| 7 | `adgroups_add` | 27 | 38 | 760 | 809 |
| 8 | `keywords_add` | 21 | 30 | 639 | 679 |
| 9 | `vcards_add` | 27 | 42 | 620 | 673 |
| 10 | `reports_custom` | 25 | 61 | 599 | 670 |
| 11 | `campaigns_get` | 20 | 38 | 541 | 590 |
| 12 | `keywords_update` | 18 | 25 | 543 | 578 |
| 13 | `ads_get` | 19 | 43 | 491 | 544 |
| 14 | `strategies_update` | 19 | 21 | 491 | 523 |
| 15 | `strategies_add` | 18 | 25 | 459 | 495 |
| 16 | `v4account_update_account` | 13 | 39 | 327 | 379 |
| 17 | `adgroups_get` | 13 | 44 | 321 | 376 |
| 18 | `agencyclients_update` | 12 | 30 | 297 | 338 |
| 19 | `bidmodifiers_add` | 12 | 37 | 285 | 333 |
| 20 | `keywords_get` | 11 | 23 | 266 | 299 |

## Главный вывод для оптимизации

`campaigns_update` + `campaigns_add` вместе = **12 548 токенов = 31%** всего
бюджета спецификации. Причина — не docstring (уже сжат), а **плоская матрица из
~210 параметров** на функцию: все 7 типов кампаний × bidding-стратегии
(Search + Network) развёрнуты в один плоский список `int|None`/`str|None`, и
FastMCP генерирует `anyOf: [..., {"type":"null"}]` 200+ раз.

Следующий шаг ([#154](https://github.com/axisrow/yandex-direct-mcp-plugin/issues/154),
второй блок) — свернуть стратегические поля в вложенные dict-параметры
(`search_strategy` / `network_strategy`), сохранив parity argv с `direct-cli`.
Потенциальный возврат: ~10–12k токенов (~25–30% бюджета).

Парето по всей поверхности (для планирования последующих этапов эпика):

| Срез | Доля бюджета |
|---|--:|
| топ-2 (`campaigns_*`) | 31% |
| топ-5 | 38% |
| топ-10 | 47% |
| топ-20 | 58% |

## Профили tool-surface (#149, этап 2)

Реализован управляемый tool surface ([#189](https://github.com/axisrow/yandex-direct-mcp-plugin/issues/189)/[#190](https://github.com/axisrow/yandex-direct-mcp-plugin/issues/190)/[#191](https://github.com/axisrow/yandex-direct-mcp-plugin/issues/191)):
можно включать/выключать группы инструментов и выбирать preset-профиль через
переменные окружения. Дефолт — `full` (все 146 тулов, обратная совместимость).

| Профиль | Tools | Бюджет (approx `len/4`) | ~% от full |
|---|--:|--:|--:|
| `full` | 146 | 34 744 | 100% |
| `core` (read-only кампаний + auth) | 10 | 2 566 | 7% |
| `analytics` (отчёты/справочники/прогнозы; без destructive/lifecycle — delete отчётов не выставляется) | 26 | ~3 600 | ~10% |
| `campaign-editor` (read+mutate кампаний/групп/объявлений/ключей/ставок, без destructive, lifecycle и финансового движения денег) | 36 | ~16 300 | ~49% |

> Абсолютные числа здесь — `approx(len/4)` (tiktoken недоступен в окружении этого
> замера из-за PEP 668), поэтому строка `full` отличается от tiktoken-базы в
> «Сводке» выше. **Проценты от full устойчивы между токенайзерами** — именно они
> показывают экономию профиля.

Как задать (env):

```bash
export YANDEX_DIRECT_TOOL_PROFILE=core            # preset-профиль
export YANDEX_DIRECT_DISABLED_GROUPS=destructive  # вычесть группу из full
export YANDEX_DIRECT_ENABLED_GROUPS=analytics     # allow-list: только эти группы
export YANDEX_DIRECT_DISABLED_TOOLS=campaigns_delete,ads_archive
```

Регрессионный guard на общий бюджет — `tests/test_token_budget.py`; разбивку по
модулю/сервису даёт `python -m tests.measure_tool_tokens`.

## Что НЕ входит в этот замер

- Стоимость самих ответов инструментов (runtime payload) — это переменная,
  не постоянная стоимость спецификации.
