"""Снятие эталонных схем stdout ``direct`` из HTTP-кассет direct-cli.

Usage: python -m tests.extract_cli_schemas [--cassettes DIR] [--out DIR]

Зачем этот скрипт
-----------------
Мок-фикстуры плагина (``tests/helpers.py::mock_runner``) задают
``runner.run_json.return_value`` вручную. Эти формы нигде не сверялись с
реальным контрактом вывода ``direct`` — issue #271. Источником истины не может
быть HTTP-кассета direct-cli напрямую: она хранит **сырой ответ API**
(``{"result": {"Campaigns": [...]}}``), а ``run_json()`` получает то, что CLI
напечатал в stdout **после** своего слоя распаковки. Между ними лежит код CLI.

Решение: прогнать настоящий бинарь ``direct`` поверх HTTP-кассет direct-cli.
Транспорт (``requests.adapters.HTTPAdapter.send``) подменяется заглушкой,
которая отдаёт записанное тело ответа, — сети и токена не нужно, живой
Yandex.Direct API не дёргается. На выходе получается подлинный stdout CLI, и
уже из него снимается **схема** (набор ключей, типы, вложенность), а не
значения: значения нестабильны и содержат коммерческие данные.

Скрипт запускается вручную при обновлении кассет direct-cli или пина
``direct-cli``; результат коммитится в ``tests/fixtures/cli_schemas/``.
Сам контрактный тест (``tests/test_mock_contract.py``) работает офлайн на
зафиксированных схемах и этот скрипт не вызывает.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_CASSETTES = (
    Path.home() / "Projects/direct-cli/tests/cassettes/test_read_cassettes"
)
DEFAULT_OUT = Path(__file__).parent / "fixtures" / "cli_schemas"

# Стабильные sandbox-фикстуры из tests/test_read_cassettes.py в direct-cli.
# Аргументы обязаны совпадать с записанными — иначе CLI соберёт другой запрос.
SANDBOX_CAMPAIGN_ID = "700012672"
ADVIDEO_PROBE_ID = "1122065647"
_TIMESTAMP = "2026-05-29T00:00:00Z"

# (cassette_id, argv для `direct`). Только readonly-команды: кассеты
# test_read_cassettes по построению не содержат мутаций.
READ_CASES: dict[str, list[str]] = {
    "campaigns_get": ["campaigns", "get"],
    "adgroups_get": ["adgroups", "get", "--campaign-ids", SANDBOX_CAMPAIGN_ID],
    "ads_get": ["ads", "get", "--campaign-ids", SANDBOX_CAMPAIGN_ID],
    "keywords_get": ["keywords", "get", "--campaign-ids", SANDBOX_CAMPAIGN_ID],
    "adextensions_get": ["adextensions", "get"],
    "adimages_get": ["adimages", "get"],
    "advideos_get": ["advideos", "get", "--ids", ADVIDEO_PROBE_ID],
    "audiencetargets_get": [
        "audiencetargets",
        "get",
        "--campaign-ids",
        SANDBOX_CAMPAIGN_ID,
    ],
    "bidmodifiers_get": ["bidmodifiers", "get", "--campaign-ids", SANDBOX_CAMPAIGN_ID],
    "bids_get": ["bids", "get", "--campaign-ids", SANDBOX_CAMPAIGN_ID],
    "businesses_get": ["businesses", "get"],
    "changes_check": [
        "changes",
        "check",
        "--campaign-ids",
        SANDBOX_CAMPAIGN_ID,
        "--timestamp",
        _TIMESTAMP,
    ],
    "changes_check_campaigns": [
        "changes",
        "check-campaigns",
        "--timestamp",
        _TIMESTAMP,
    ],
    "changes_check_dictionaries": ["changes", "check-dictionaries"],
    "clients_get": ["clients", "get"],
    "creatives_get": ["creatives", "get", "--ids", "1"],
    "dictionaries_get": ["dictionaries", "get", "--names", "Currencies,GeoRegions"],
    "dynamicads_get": ["dynamicads", "get", "--campaign-ids", SANDBOX_CAMPAIGN_ID],
    "dynamicfeedadtargets_get": [
        "dynamicfeedadtargets",
        "get",
        "--campaign-ids",
        SANDBOX_CAMPAIGN_ID,
    ],
    "feeds_get": ["feeds", "get"],
    "keywordbids_get": ["keywordbids", "get", "--campaign-ids", SANDBOX_CAMPAIGN_ID],
    "leads_get": ["leads", "get", "--turbo-page-ids", "1"],
    "negativekeywordsharedsets_get": ["negativekeywordsharedsets", "get"],
    "retargeting_get": ["retargeting", "get"],
    "sitelinks_get": ["sitelinks", "get"],
    "smartadtargets_get": [
        "smartadtargets",
        "get",
        "--campaign-ids",
        SANDBOX_CAMPAIGN_ID,
    ],
    "strategies_get": ["strategies", "get", "--ids", "1"],
    "turbopages_get": ["turbopages", "get"],
    "vcards_get": ["vcards", "get"],
    "v4forecast_list": ["v4forecast", "list"],
    "v4goals_get_stat_goals": [
        "v4goals",
        "get-stat-goals",
        "--campaign-ids",
        SANDBOX_CAMPAIGN_ID,
    ],
    "v4tags_get_campaigns": [
        "v4tags",
        "get-campaigns",
        "--campaign-ids",
        SANDBOX_CAMPAIGN_ID,
    ],
    "v4wordstat_list_reports": ["v4wordstat", "list-reports"],
}

# sitecustomize, подменяющий транспорт requests записанным телом ответа.
# Патчится HTTPAdapter.send, а не Session.request: адаптеру передаётся уже
# собранный PreparedRequest, который requests требует видеть в Response.request.
_STUB_SITECUSTOMIZE = """
import os
import yaml
import requests
from requests.adapters import HTTPAdapter

_interactions = yaml.safe_load(open(os.environ["DIRECT_CASSETTE"]))["interactions"]
_cursor = {"n": 0}


def _send(self, request, **kwargs):
    # Кассеты записаны как строгая последовательность запросов одной команды;
    # последнее взаимодействие переиспользуется, если CLI ретраит.
    interaction = _interactions[min(_cursor["n"], len(_interactions) - 1)]
    _cursor["n"] += 1
    response = requests.Response()
    response.status_code = interaction["response"]["status"]["code"]
    response._content = interaction["response"]["body"]["string"].encode()
    response.url = request.url
    response.request = request
    response.encoding = "utf-8"
    response.headers["Content-Type"] = "application/json"
    return response


HTTPAdapter.send = _send
"""


def schema_of(value: Any) -> Any:
    """Свести значение к схеме: типы, ключи, вложенность — без самих данных.

    Списки сворачиваются в одноэлементный список со схемой, объединяющей все
    элементы: длина выборки в sandbox нестабильна, а форма элемента — нет.
    """
    if isinstance(value, dict):
        return {key: schema_of(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        if not value:
            return []
        merged: dict[str, Any] = {}
        non_dict: list[Any] = []
        for item in value:
            item_schema = schema_of(item)
            if isinstance(item_schema, dict):
                merged.update(item_schema)
            else:
                non_dict.append(item_schema)
        if merged and not non_dict:
            return [merged]
        return [non_dict[0]] if non_dict else [merged]
    if value is None:
        # null в JSON не несёт информации о типе поля; помечаем отдельно, чтобы
        # nullable-поле не выглядело сменой типа при повторном снятии.
        return "null"
    return type(value).__name__


def _write_stub(stub_dir: Path) -> None:
    stub_dir.mkdir(parents=True, exist_ok=True)
    (stub_dir / "sitecustomize.py").write_text(_STUB_SITECUSTOMIZE, encoding="utf-8")


def extract(cassettes: Path, out: Path, stub_dir: Path) -> int:
    """Снять схемы для всех READ_CASES. Возвращает количество ошибок."""
    _write_stub(stub_dir)
    out.mkdir(parents=True, exist_ok=True)
    failures = 0

    for cassette_id, argv in sorted(READ_CASES.items()):
        cassette = cassettes / f"test_read_command[{cassette_id}].yaml"
        if not cassette.exists():
            # Не SKIP: пропавшая (переименованная выше по течению) кассета
            # оставила бы на диске эталон от прошлого прогона, а тест считает
            # эталоны истиной и подгонять их запрещено. Протухший эталон —
            # худший режим отказа, поэтому это ошибка, а не пропуск.
            print(f"FAIL {cassette_id}: кассета не найдена ({cassette})")
            failures += 1
            continue

        env = dict(
            os.environ,
            DIRECT_CASSETTE=str(cassette),
            PYTHONPATH=str(stub_dir),
        )
        proc = subprocess.run(
            [
                "direct",
                "--sandbox",
                "--token",
                "REPLAY_DUMMY_TOKEN",
                *argv,
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        if proc.returncode != 0:
            print(f"FAIL {cassette_id}: rc={proc.returncode}\n{proc.stderr[:400]}")
            failures += 1
            continue
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            print(f"FAIL {cassette_id}: stdout не JSON ({exc})\n{proc.stdout[:200]}")
            failures += 1
            continue

        document = {
            "cassette_id": cassette_id,
            "argv": argv,
            "schema": schema_of(payload),
        }
        (out / f"{cassette_id}.json").write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"OK   {cassette_id}")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cassettes", type=Path, default=DEFAULT_CASSETTES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--stub-dir",
        type=Path,
        default=Path(os.environ.get("TMPDIR", "/tmp")) / "direct_schema_stub",
    )
    ns = parser.parse_args()

    if not ns.cassettes.exists():
        print(f"Кассеты direct-cli не найдены: {ns.cassettes}", file=sys.stderr)
        return 2
    return 1 if extract(ns.cassettes, ns.out, ns.stub_dir) else 0


if __name__ == "__main__":
    raise SystemExit(main())
