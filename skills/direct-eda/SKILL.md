---
name: direct-eda
description: "Разведочный анализ (EDA) статистики Яндекс.Директ поверх отчётов. Используется когда пользователь просит проанализировать статистику/данные, найти тренды или аномалии, построить разрез по времени/устройствам/гео/полу-возрасту, выбрать топ/антитоп кампаний, ключей или объявлений, оценить эффективность (CTR, CR, CPA, ROAS) и дать выводы/рекомендации."
user-invocable: true
argument-hint: "[что анализируем: период, разрез, метрика — напр. «расход по месяцам за год» или «топ-20 ключей по CPA»]"
---

# Разведочный анализ статистики Яндекс.Директ (EDA)

Скилл для исследования статистики кампаний через отчётные MCP-инструменты плагина.
Не вводит новых API-методов — это композиция `reports_get` / `reports_custom` /
`reports_list_types` (+ `v4goals_get_stat_goals` для целей) с правильным выбором
разреза, метрик и подачи выводов.

## С чего начинать

1. **Авторизация.** Сначала `auth_status()`. Если `valid: false` — `auth_login()`.
   Без авторизации отчёты вернут ошибку.
2. **Выбор инструмента:**
   - `reports_get(date_from, date_to)` — быстрый снимок по кампаниям за короткое
     окно (по умолчанию ~8 дней, дефолтные поля). Для ответа «как там кампании».
   - `reports_custom(field_names=…)` — всё остальное: произвольные поля, разрезы
     по времени/срезам, фильтры, сортировка, цели, пагинация, выгрузка в файл.
   - `reports_list_types()` — если не уверен, какой `report_type` подходит.
3. **Сомневаешься в полях/фильтрах — `dry_run=True`.** Reports API отвергает
   неверные enum'ы опаковым `error_code=8000`; локальный dry-run экономит раунд-трип
   и показывает итоговый `request_body`.

## Типовые рецепты EDA

`report_type` по умолчанию = `CUSTOM_REPORT` (самый широкий набор измерений).
Деньги по умолчанию в рублях (не микро). `field_names` — регистрозависимый enum.

| Вопрос | Как получить |
|---|---|
| Общий снимок по кампаниям | `reports_get()` (или `reports_custom` с `CampaignName,Impressions,Clicks,Cost,Conversions,Ctr,AvgCpc`) |
| Динамика по месяцам/неделям/дням | `field_names="Month,Cost,Clicks,Conversions,…"`, `order_by=["Month:ASC"]` (или `Week`/`Date`) |
| Топ-N кампаний по расходу/конверсиям | `field_names="CampaignName,Cost,Clicks,Conversions,CostPerConversion"`, `order_by=["Cost:DESC"]`, `page_limit=N` |
| Топ-N ключевых фраз | `report_type="CRITERIA_PERFORMANCE_REPORT"`, `field_names="CampaignName,Criterion,Clicks,Cost,Ctr,Conversions"`, `order_by=["Cost:DESC"]`, `page_limit=N` |
| Разрез по устройствам | `field_names="Device,Cost,Clicks,Ctr,Conversions,CostPerConversion"` |
| Разрез по площадкам (Поиск/Сети) | `field_names="AdNetworkType,Cost,Clicks,Ctr,Conversions"` |
| Пол / возраст | `field_names="Gender,Age,Impressions,Clicks,Ctr,Conversions"` |
| География | `field_names="LocationOfPresenceName,Cost,Clicks,Conversions"` (или `TargetingLocationName`) |
| Поисковые запросы (для минус-слов / новых ключей) | `report_type="SEARCH_QUERY_PERFORMANCE_REPORT"`, `field_names="Query,Impressions,Clicks,Ctr,Cost,Conversions"`, `order_by=["Cost:DESC"]` |
| Конверсии по целям Метрики | задай `goal_ids="123,456"` → в выводе появятся `Conversions_<goal>_<attr>` и `CostPerConversion_<goal>_<attr>`. ID целей: `v4goals_get_stat_goals(campaign_ids=…)` |
| Итоги по всему аккаунту | `report_type="ACCOUNT_PERFORMANCE_REPORT"` |

Период: либо `date_from`/`date_to` (YYYY-MM-DD), либо пресет `date_range_type`
(`last_7_days`, `last_30_days`, `last_3_months`, `last_week`, `last_5_years`, …) —
**одно из двух**, не вместе. Для «за 2 года» передавай явные даты (пресета
`last_2_years` нет).

## Метрики и производные KPI

Базовые поля API: `Impressions`, `Clicks`, `Cost`, `Ctr`, `AvgCpc`, `Conversions`,
`ConversionRate`, `CostPerConversion`, `Revenue`, `BounceRate`, `AvgPageviews`,
`AvgImpressionPosition`. Чего нет в API — считай сам из выгрузки:

- **CTR** = Clicks / Impressions; **CR** = Conversions / Clicks;
- **CPC** = Cost / Clicks; **CPA (CPL)** = Cost / Conversions;
- **ROAS** = Revenue / Cost; **CRR** = Cost / Revenue (доля рекламных расходов);
- **доля расхода** кампании = Cost_i / Σ Cost.

Берёшь сырые `Impressions/Clicks/Cost/Conversions/Revenue` нужным разрезом и
агрегируешь/делишь на стороне анализа — так точнее, чем доверять предсчитанным
полям на мелких выборках (деление на ноль, округления).

## Поиск аномалий (что искать)

- **Скачки расхода**: динамика `Cost` по `Date`/`Week` — всплески/обвалы > N% к
  соседнему периоду или к скользящему среднему.
- **Падение эффективности**: рост `CostPerConversion` / падение `ConversionRate`
  или `Ctr` период-к-периоду (сравни два окна одинаковой длины).
- **Расход без конверсий**: строки с `Cost>0` и `Conversions=0` (фильтр
  `["Clicks:GREATER_THAN:0"]`, затем смотри нулевые конверсии) — кандидаты в стоп
  или в минус-слова (через `SEARCH_QUERY_PERFORMANCE_REPORT`).
- **Концентрация**: 80/20 — какие кампании/ключи дают основной расход и
  основную конверсию (часто это разные множества).
- **Аномальные срезы**: устройство/гео/демография с CPA в разы выше среднего.

Для сравнения «период к периоду» делай два запроса с равными окнами (напр.
`last_7_days` и предыдущая неделя явными датами) и считай дельты.

## Большие выгрузки и подача

- **Большой отчёт** (>5k строк или > ~6 мес): `output_path="/tmp/…json"` —
  инструмент вернёт `{output_path, rows_written, …}`, дальше читай файл обычными
  файловыми инструментами и анализируй локально. Допустимые корни пути — системный
  temp или `$CLAUDE_PLUGIN_DATA`.
- **Формат**: `response_format="json"` (по умолчанию, удобно для разбора) или
  `csv`/`tsv`/`table`.
- **Подача вывода пользователю**: сначала короткий вывод (1–3 факта/инсайта),
  затем таблица с числами, затем конкретные рекомендации к действию (что усилить,
  что остановить, где добавить минус-слова/скорректировать ставки). Цифры приводи
  с единицами (₽, %, шт.) и за какой период.

## Подводные камни

- **Цели — только через `goal_ids`**, не через `filters` (`Goals:`-фильтр API не
  поддерживает; инструмент его отклонит).
- `filters` **перекрывают** `campaign_ids`/`adgroup_ids` (direct-cli применит
  фильтры и проигнорирует селекторы). Нужен и срез по кампаниям, и фильтр — вырази
  кампании фильтром: `["CampaignId:IN:111,222"]`.
- `field_names` — **регистрозависимый enum**, зависящий от `report_type`. Не уверен —
  `dry_run=True` или `reports_list_types()`.
- `campaign_ids`/`adgroup_ids`/`goal_ids` — **≤10** на запрос.
- Атрибуция: дефолтный код в per-goal колонках — `LSC`; нужен другой — задай
  `attribution_models` (`FC,LC,LSC,LYDC,…`).
- НДС/скидка: `include_vat`/`include_discount` берут настройку аккаунта, если не
  заданы явно — учитывай при сравнении «расхода» с биллингом.

## Связанные навыки

- Управление сущностями (создать/изменить кампании, ставки и т.п.) — навык
  `yandex-direct`.
- Написание текстов объявлений по итогам анализа — навык `direct-ads`.
