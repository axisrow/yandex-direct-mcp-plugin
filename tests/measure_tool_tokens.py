"""Воспроизводимый измеритель «веса» MCP-инструментов в токенах.

Считает то, что реально уходит в контекст модели при инициализации MCP:
для каждого инструмента — name + description + inputSchema (JSON Schema
параметров). Это постоянная стоимость, которая платится на каждом запросе,
пока плагин подключён.

Запуск:
    python -m tests.measure_tool_tokens            # сводка + топ-20
    python -m tests.measure_tool_tokens --json     # полный JSON по всем тулам

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


async def collect_rows():
    from server.main import mcp

    count, method = _make_counter()
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
                "n_params": len(props),
                "desc_tok": count(desc),
                "schema_tok": count(schema_json),
                "total_tok": count(payload),
            }
        )
    rows.sort(key=lambda r: r["total_tok"], reverse=True)
    return rows, method


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


def main():
    rows, method = asyncio.run(collect_rows())
    s = summarize(rows, method)

    if "--json" in sys.argv:
        print(json.dumps({**s, "rows": rows}, ensure_ascii=False, indent=2))
        return

    print(f"Способ оценки: {s['method']}")
    print(f"Инструментов: {s['n_tools']}")
    print(f"Суммарно токенов (спецификация): {s['total_tok']:,}")
    print(f"  descriptions: {s['total_desc_tok']:,}")
    print(f"  JSON Schema:  {s['total_schema_tok']:,}")
    print(f"Среднее на инструмент: {s['total_tok'] // max(s['n_tools'], 1):,}")
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
