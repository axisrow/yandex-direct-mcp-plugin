"""Воспроизводимый измеритель «веса» MCP-инструментов в токенах.

Считает то, что реально уходит в контекст модели при инициализации MCP:
для каждого инструмента — name + description + inputSchema (JSON Schema
параметров). Это постоянная стоимость, которая платится на каждом запросе,
пока плагин подключён.

Запуск:
    python -m tests.measure_tool_tokens            # сводка + rollup + топ-20
    python -m tests.measure_tool_tokens --json     # полный JSON по всем тулам

Помимо общей суммы выводит rollup — вклад **по модулю** (`server/tools/*.py`)
и **по сервису** (`cli_service` из `server/contract.py`), чтобы видеть, какие
семейства инструментов дают основную стоимость.

Оценка токенов:
    - если установлен tiktoken — кодировка cl100k_base (близко к токенайзеру Claude, ±~10%);
    - иначе — приближение len(text) / 4 (грубее, но без зависимостей).
Способ оценки печатается в выводе, чтобы цифры были сопоставимы между запусками.
"""

from __future__ import annotations

import asyncio
import json
import sys


def _make_counter():
    """Вернуть (функция_подсчёта, метка_способа)."""
    try:
        # tiktoken is optional and intentionally not a project dependency;
        # the except-branch below falls back to a dependency-free estimate.
        import tiktoken  # type: ignore[import-not-found]

        enc = tiktoken.get_encoding("cl100k_base")
        return (lambda s: len(enc.encode(s or "")), "tiktoken/cl100k_base")
    except Exception:
        # Приближение: ~4 символа на токен. Достаточно для сравнения «до/после».
        return (lambda s: (len(s or "") + 3) // 4, "approx(len/4)")


def _module_by_name(mcp) -> dict[str, str]:
    """Сопоставить имя инструмента модулю, где определена его функция.

    Берём `fn.__module__` из реестра FastMCP и срезаем префикс
    `server.tools.`. Реестр — внутренний атрибут библиотеки mcp; это
    измеритель, а не прод-код, поэтому доступ к приватному полю допустим и
    обёрнут в безопасные getattr-фолбэки.
    """
    manager = getattr(mcp, "_tool_manager", None)
    registry = getattr(manager, "_tools", {}) if manager is not None else {}
    mapping: dict[str, str] = {}
    for name, tool in registry.items():
        fn = getattr(tool, "fn", None)
        module = getattr(fn, "__module__", "") or ""
        if module.startswith("server.tools."):
            module = module[len("server.tools.") :]
        mapping[name] = module or "(unknown)"
    return mapping


def _service_by_name() -> dict[str, str]:
    """Сопоставить имя инструмента его `cli_service` из публичного контракта."""
    from server.contract import PUBLIC_CONTRACT

    return {ct.public_name: (ct.cli_service or "(plugin)") for ct in PUBLIC_CONTRACT}


async def collect_rows():
    from server.main import mcp

    count, method = _make_counter()
    module_by_name = _module_by_name(mcp)
    service_by_name = _service_by_name()
    tools = await mcp.list_tools()
    rows = []
    for t in tools:
        name = t.name
        desc = t.description or ""
        schema = t.inputSchema or {}
        schema_json = json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
        payload = json.dumps(
            {"name": name, "description": desc, "input_schema": schema},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        props = schema.get("properties") or {}
        rows.append(
            {
                "name": name,
                "module": module_by_name.get(name, "(unknown)"),
                "service": service_by_name.get(name, "(plugin)"),
                "n_params": len(props),
                "desc_tok": count(desc),
                "schema_tok": count(schema_json),
                "total_tok": count(payload),
            }
        )
    rows.sort(key=lambda r: r["total_tok"], reverse=True)
    return rows, method


def rollup(rows, key):
    """Сгруппировать строки по `key` (module/service) и просуммировать токены."""
    groups: dict[str, dict] = {}
    for r in rows:
        bucket = groups.setdefault(
            r[key],
            {key: r[key], "n_tools": 0, "desc_tok": 0, "schema_tok": 0, "total_tok": 0},
        )
        bucket["n_tools"] += 1
        bucket["desc_tok"] += r["desc_tok"]
        bucket["schema_tok"] += r["schema_tok"]
        bucket["total_tok"] += r["total_tok"]
    return sorted(groups.values(), key=lambda b: b["total_tok"], reverse=True)


def summarize(rows, method):
    total = sum(r["total_tok"] for r in rows)
    total_desc = sum(r["desc_tok"] for r in rows)
    total_schema = sum(r["schema_tok"] for r in rows)
    return {
        "method": method,
        "n_tools": len(rows),
        "total_tok": total,
        "total_desc_tok": total_desc,
        "total_schema_tok": total_schema,
    }


def _print_rollup(title, buckets, key):
    print(title)
    print(f"{key:<26} {'tools':>5} {'desc':>7} {'schema':>8} {'TOTAL':>8} {'%':>5}")
    grand = sum(b["total_tok"] for b in buckets) or 1
    for b in buckets:
        share = 100 * b["total_tok"] / grand
        print(
            f"{b[key]:<26} {b['n_tools']:>5} {b['desc_tok']:>7} "
            f"{b['schema_tok']:>8} {b['total_tok']:>8} {share:>4.0f}%"
        )


def main():
    rows, method = asyncio.run(collect_rows())
    s = summarize(rows, method)
    by_module = rollup(rows, "module")
    by_service = rollup(rows, "service")

    if "--json" in sys.argv:
        print(
            json.dumps(
                {**s, "by_module": by_module, "by_service": by_service, "rows": rows},
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    print(f"Способ оценки: {s['method']}")
    print(f"Инструментов: {s['n_tools']}")
    print(f"Суммарно токенов (спецификация): {s['total_tok']:,}")
    print(f"  descriptions: {s['total_desc_tok']:,}")
    print(f"  JSON Schema:  {s['total_schema_tok']:,}")
    print(f"Среднее на инструмент: {s['total_tok'] // max(s['n_tools'], 1):,}")
    print()
    _print_rollup("По модулю (server/tools/*.py):", by_module, "module")
    print()
    _print_rollup("По сервису (cli_service):", by_service, "service")
    print()
    print("ТОП-20 по весу:")
    print(f"{'#':>3} {'tool':<42} {'params':>6} {'desc':>6} {'schema':>7} {'TOTAL':>7}")
    for i, r in enumerate(rows[:20], 1):
        print(
            f"{i:>3} {r['name']:<42} {r['n_params']:>6} "
            f"{r['desc_tok']:>6} {r['schema_tok']:>7} {r['total_tok']:>7}"
        )


if __name__ == "__main__":
    main()
