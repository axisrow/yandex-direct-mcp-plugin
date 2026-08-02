"""Контрактный тест: формы мок-фикстур против реального выхлопа ``direct`` (#271).

Проблема
--------
``tests/helpers.py::mock_runner`` задаёт ``runner.run_json.return_value``
вручную. Входная сторона (argv) покрыта системно, а **выходная** — нет: если
CLI сменит форму stdout, мок-тесты останутся зелёными и соврут.

Источник истины
---------------
Эталоны в ``tests/fixtures/cli_schemas/`` сняты со stdout **настоящего**
бинаря ``direct``, прогнанного поверх HTTP-кассет direct-cli с подменённым
транспортом (см. ``tests/extract_cli_schemas.py``). Это принципиально: сама
HTTP-кассета хранит сырой ответ API (``{"result": {"Campaigns": [...]}}``), а
``run_json()`` получает то, что CLI напечатал **после** своего слоя распаковки
(``[{...}]``). Сверять мок с HTTP-кассетой напрямую нельзя — между ними лежит
код CLI.

Что именно проверяется
----------------------
Фиксируется **схема**, а не значения: значения нестабильны и утекают как
коммерческие данные. Основное утверждение — **тип верхнеуровневого
контейнера** (список против объекта): именно на нём мок расходится с CLI
незаметно. Тип контейнера не формальность — например ``campaigns_list``
(``server/tools/campaigns.py``) фильтрует результат через
``isinstance(result, list)``, поэтому мок-объект вместо списка молча уводит
тест мимо ветки фильтрации.

Формы моков не дублируются таблицей, а **вычитываются из самих тестов**
через AST: захардкоженный список разошёлся бы с реальностью ровно так же
незаметно, как и сами моки.

Тест офлайн и детерминированный: читает только исходники тестов и
зафиксированные JSON-схемы. Ни сети, ни токена, ни бинаря ``direct``.

Покрытие
--------
Покрыты readonly ``get``-команды, для которых у direct-cli есть кассеты
(33 команды, ``READ_CASES`` в ``tests/extract_cli_schemas.py``), плюс формы
мутаций ``AddResults``/``UpdateResults`` — структурно. Не покрыто: команды без
кассет в direct-cli, отчёты (TSV, не JSON), а также элементный состав тех
ответов, где sandbox вернул пустой список (форма контейнера проверяется,
набор полей элемента — нет).
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest

TESTS_DIR = Path(__file__).parent
SCHEMAS_DIR = TESTS_DIR / "fixtures" / "cli_schemas"

# Тулы плагина → cassette_id эталона. Ключ — имя функции-тула, как она
# вызывается в тестах; так мок связывается с командой CLI, которую тул строит.
TOOL_TO_CASSETTE: dict[str, str] = {
    "campaigns_list": "campaigns_get",
    "adgroups_list": "adgroups_get",
    "ads_list": "ads_get",
    "keywords_list": "keywords_get",
    "clients_get": "clients_get",
    "advideos_get": "advideos_get",
    "retargeting_list": "retargeting_get",
    "sitelinks_list": "sitelinks_get",
    "vcards_list": "vcards_get",
    "bidmodifiers_list": "bidmodifiers_get",
    "feeds_list": "feeds_get",
    "leads_list": "leads_get",
    "businesses_list": "businesses_get",
    "turbo_pages_list": "turbopages_get",
    "keyword_bids_list": "keywordbids_get",
    "negative_keyword_shared_sets_list": "negativekeywordsharedsets_get",
    "smart_ad_targets_list": "smartadtargets_get",
    "dynamic_ads_list": "dynamicads_get",
    "audience_targets_list": "audiencetargets_get",
    "adextensions_list": "adextensions_get",
    "adimages_list": "adimages_get",
    "creatives_list": "creatives_get",
    "strategies_list": "strategies_get",
    "v4goals_get_stat_goals": "v4goals_get_stat_goals",
    "v4tags_get_campaigns": "v4tags_get_campaigns",
    "v4forecast_list": "v4forecast_list",
    "v4wordstat_list_reports": "v4wordstat_list_reports",
    "changes_check": "changes_check",
    "changes_checkcamp": "changes_check_campaigns",
    "changes_checkdict": "changes_check_dictionaries",
    "dictionaries_get": "dictionaries_get",
}

# Команды, у которых CLI НЕ распаковывает конверт ``result``.
ENVELOPED = {
    "changes_check",
    "changes_check_campaigns",
    "changes_check_dictionaries",
    "dictionaries_get",
}


def load_schema(cassette_id: str) -> Any:
    """Вернуть зафиксированную схему stdout ``direct`` для команды."""
    path = SCHEMAS_DIR / f"{cassette_id}.json"
    assert path.exists(), (
        f"Нет эталонной схемы {path.name}. "
        "Пересними: python -m tests.extract_cli_schemas"
    )
    return json.loads(path.read_text(encoding="utf-8"))["schema"]


def container_kind(value: Any) -> str:
    """Тип верхнеуровневого контейнера: 'list' | 'dict' | 'scalar'."""
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return "scalar"


def _literal_container(node: ast.AST) -> str | None:
    """Тип контейнера у литерального аргумента ``mock_runner(...)``.

    Возвращает None для нелитеральных форм (переменная, вызов, ``None``) —
    их статически связать с командой нельзя, они пропускаются.
    """
    if isinstance(node, ast.List):
        return "list"
    if isinstance(node, ast.Dict):
        return "dict"
    return None


def _is_dry_run_test(func: ast.FunctionDef) -> bool:
    """Тест прогоняет тул в режиме ``dry_run``?

    В dry-run CLI печатает не выхлоп команды, а конверт с описанием запроса
    (``{"method": ..., ...}``) — это отдельный контракт, и сверять его с
    эталоном обычной команды бессмысленно.
    """
    for node in ast.walk(func):
        if isinstance(node, ast.keyword) and node.arg == "dry_run":
            return True
    return False


def _collect_mock_sites() -> list[tuple[str, str, str, int]]:
    """Найти в тестах связки «mock_runner(<литерал>) → вызванный тул».

    Возвращает (tool_name, container_kind, файл, строка). Связывание — по
    телу функции: мок, созданный в тесте, относится к тулу, который этот тест
    вызывает. Тесты, вызывающие несколько разных тулов из ``TOOL_TO_CASSETTE``,
    пропускаются как неоднозначные.
    """
    sites: list[tuple[str, str, str, int]] = []

    for path in sorted(TESTS_DIR.glob("test_*.py")):
        if path.name == "test_mock_contract.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        for func in ast.walk(tree):
            if not isinstance(func, ast.FunctionDef):
                continue

            mocks: list[tuple[str, int]] = []
            tools: set[str] = set()
            for node in ast.walk(func):
                if not isinstance(node, ast.Call):
                    continue
                name = node.func.id if isinstance(node.func, ast.Name) else None
                if name == "mock_runner" and node.args:
                    kind = _literal_container(node.args[0])
                    if kind is not None:
                        mocks.append((kind, node.lineno))
                elif name in TOOL_TO_CASSETTE:
                    tools.add(name)

            if len(tools) != 1 or not mocks or _is_dry_run_test(func):
                continue
            tool = tools.pop()
            for kind, lineno in mocks:
                sites.append(
                    (tool, kind, str(path.relative_to(TESTS_DIR.parent)), lineno)
                )

    return sites


MOCK_SITES = _collect_mock_sites()


def test_mock_sites_were_discovered() -> None:
    """Страховка: AST-обход действительно что-то нашёл.

    Без неё переименование ``mock_runner`` превратило бы весь контрактный
    тест в пустую параметризацию, молча зелёную.
    """
    assert len(MOCK_SITES) >= 20, (
        f"Найдено лишь {len(MOCK_SITES)} мок-фикстур — обход сломался?"
    )


@pytest.mark.parametrize(
    ("tool", "kind", "source", "lineno"),
    MOCK_SITES,
    ids=[f"{t}:{Path(s).stem}:{n}" for t, _, s, n in MOCK_SITES],
)
def test_mock_container_matches_cli_stdout(
    tool: str, kind: str, source: str, lineno: int
) -> None:
    """Тип контейнера мок-фикстуры совпадает с реальным stdout ``direct``."""
    cassette_id = TOOL_TO_CASSETTE[tool]
    reference = load_schema(cassette_id)
    expected = container_kind(reference)
    assert kind == expected, (
        f"{source}:{lineno}: мок для {tool}() отдаёт {kind}, "
        f"а `direct {' '.join(cassette_id.split('_'))}` печатает {expected} "
        f"(эталон: {json.dumps(reference, ensure_ascii=False)[:200]}). "
        "Почини мок — эталон снят с настоящего CLI, подгонять его нельзя."
    )


@pytest.mark.parametrize("cassette_id", sorted(ENVELOPED))
def test_result_envelope_is_not_unwrapped(cassette_id: str) -> None:
    """``changes``/``dictionaries`` печатают конверт ``result`` как есть.

    Регрессия на распаковку: если CLI начнёт снимать ``result`` и здесь,
    тулы плагина, ожидающие конверт, поедут — это должно падать шумно.
    """
    reference = load_schema(cassette_id)
    assert isinstance(reference, dict) and set(reference) == {"result"}, (
        f"[{cassette_id}] ожидался конверт {{'result': ...}}, "
        f"а эталон: {json.dumps(reference, ensure_ascii=False)[:200]}"
    )


def test_get_commands_return_bare_list() -> None:
    """Все прочие ``get``-команды печатают распакованный список.

    Обратная сторона предыдущего теста: если CLI начнёт оборачивать выхлоп
    ``get`` в конверт, мок-фикстуры со списком станут ложью.
    """
    offenders = []
    for path in sorted(SCHEMAS_DIR.glob("*.json")):
        if path.stem in ENVELOPED:
            continue
        schema = json.loads(path.read_text(encoding="utf-8"))["schema"]
        if not isinstance(schema, list):
            offenders.append((path.stem, container_kind(schema)))
    assert not offenders, f"get-команды с неожиданным контейнером: {offenders}"


def test_every_mapped_tool_has_a_schema() -> None:
    """Каждая команда из карты тулов имеет зафиксированный эталон."""
    missing = sorted(
        cassette_id
        for cassette_id in set(TOOL_TO_CASSETTE.values())
        if not (SCHEMAS_DIR / f"{cassette_id}.json").exists()
    )
    assert not missing, f"нет эталонных схем: {missing}"


# Тулы, у которых нет ни одной литеральной мок-фикстуры: их тесты передают
# в mock_runner() модульную константу (SAMPLE_KEYWORDS, mock_sitelinks, ...),
# а её AST статически не развернуть. Это осознанный пропуск, а не дыра.
TOOLS_WITHOUT_LITERAL_MOCKS = {
    "keywords_list",
    "sitelinks_list",
    "vcards_list",
    "adextensions_list",
    "adimages_list",
    "creatives_list",
    "strategies_list",
    "v4forecast_list",
    "changes_check",
    "changes_checkdict",
}


def test_no_orphan_schemas() -> None:
    """Каждый закоммиченный эталон соответствует кейсу снятия.

    Осиротевший файл — признак, что кассету выше по течению переименовали
    или удалили, а эталон остался протухшим. Тест считает эталоны истиной,
    поэтому такой файл должен обнаруживаться, а не тихо переживать прогоны.
    """
    from tests.extract_cli_schemas import READ_CASES

    orphans = sorted(
        path.stem for path in SCHEMAS_DIR.glob("*.json") if path.stem not in READ_CASES
    )
    assert not orphans, (
        f"эталоны без кейса в READ_CASES: {orphans}. "
        "Кассету переименовали/удалили выше по течению? Пересними схемы."
    )


def test_every_mapped_tool_name_is_real() -> None:
    """Каждый ключ карты — имя существующего тула, реально дающее сайты.

    Эта проверка появилась из-за конкретного бага: шесть ключей были
    выведены из cassette_id (``turbopages_list``) вместо чтения
    ``server/tools`` (``turbo_pages_list``). Такие ключи не совпадают ни с
    одним вызовом, поэтому молча покрывают ноль сайтов — тест зелёный, а
    покрытия нет. Именно так осталось незамеченным расхождение
    ``{"turboPages": []}`` в ``tests/test_turbo_pages.py``.
    """
    covered = {tool for tool, _, _, _ in MOCK_SITES}
    dead = sorted(
        tool
        for tool in TOOL_TO_CASSETTE
        if tool not in covered and tool not in TOOLS_WITHOUT_LITERAL_MOCKS
    )
    assert not dead, (
        f"ключи карты не дали ни одного сайта: {dead}. "
        "Либо имя тула написано неверно (сверь с server/tools/), либо у тула "
        "нет литеральных моков — тогда внеси его в TOOLS_WITHOUT_LITERAL_MOCKS."
    )


# ── Мутации ────────────────────────────────────────────────────────────────
# У direct-cli нет кассет на мутации (test_read_cassettes по построению
# readonly), но форма ``AddResults``/``UpdateResults`` — это контракт WSDL v5,
# а не выдумка CLI: операция возвращает объект с массивом per-item результатов,
# каждый со своим ``Id``. Проверяем структурно, по формам из самих тестов.
MUTATION_KEYS = ("AddResults", "UpdateResults")


def _collect_mutation_shapes() -> list[tuple[str, str, int, str]]:
    """Собрать литеральные моки вида ``{"AddResults": [...]}`` из тестов."""
    found: list[tuple[str, str, int, str]] = []
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        if path.name == "test_mock_contract.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "mock_runner"
                and node.args
                and isinstance(node.args[0], ast.Dict)
            ):
                continue
            literal = node.args[0]
            for key_node, value_node in zip(literal.keys, literal.values):
                if (
                    isinstance(key_node, ast.Constant)
                    and key_node.value in MUTATION_KEYS
                ):
                    found.append(
                        (
                            key_node.value,
                            str(path.relative_to(TESTS_DIR.parent)),
                            node.lineno,
                            ast.dump(value_node),
                        )
                    )
    return found


MUTATION_SITES = _collect_mutation_shapes()


def test_mutation_sites_were_discovered() -> None:
    """Страховка от пустой параметризации мутаций."""
    assert MUTATION_SITES, "не найдено ни одного мока AddResults/UpdateResults"


@pytest.mark.parametrize(
    ("key", "source", "lineno", "dumped"),
    MUTATION_SITES,
    ids=[f"{k}:{Path(s).stem}:{n}" for k, s, n, _ in MUTATION_SITES],
)
def test_mutation_result_is_per_item_list(
    key: str, source: str, lineno: int, dumped: str
) -> None:
    """Мутации отдают объект с массивом per-item результатов.

    Скалярное значение вместо массива (``{"AddResults": {"Id": 1}}``) —
    расхождение с контрактом v5, которое иначе никто не поймает.
    """
    assert dumped.startswith("List("), (
        f"{source}:{lineno}: {key} должен быть массивом per-item результатов, "
        f"а мок отдаёт {dumped[:60]}"
    )
