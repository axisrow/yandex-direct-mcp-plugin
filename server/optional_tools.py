"""Opt-in import gate for tool bundles that are absent from the default surface.

FastMCP registers decorated tools eagerly while their modules are imported.  To
keep optional tool schemas out of the default MCP context, module selection must
therefore happen before import rather than by removing tools afterwards.
"""

from __future__ import annotations

import importlib
from collections.abc import Mapping

from server.contract import OPTIONAL_TOOL_NAMES

ENV_OPTIONAL_TOOLS = "YANDEX_DIRECT_OPTIONAL_TOOLS"

# Keep both bundle and module order stable: FastMCP preserves registration order
# in tools/list, which helps clients reuse prompt caches across server restarts.
OPTIONAL_BUNDLES: dict[str, tuple[str, ...]] = {
    "browser": (
        "server.tools.masters",
        "server.tools.history",
    ),
    "trackingparams": ("server.tools.trackingparams",),
}


def _configured_bundles(env: Mapping[str, str]) -> frozenset[str]:
    raw = env.get(ENV_OPTIONAL_TOOLS, "")
    return frozenset(item.strip().lower() for item in raw.split(",") if item.strip())


def enabled_bundles(env: Mapping[str, str]) -> frozenset[str]:
    """Return known bundles enabled by ``env``; ``all`` expands every bundle."""
    configured = _configured_bundles(env)
    if "all" in configured:
        return frozenset(OPTIONAL_BUNDLES)
    return frozenset(configured & OPTIONAL_BUNDLES.keys())


def optional_tools_warnings(env: Mapping[str, str]) -> list[str]:
    """Return warnings for unknown optional bundle names."""
    unknown = _configured_bundles(env) - OPTIONAL_BUNDLES.keys() - {"all"}
    if not unknown:
        return []
    return [
        (
            f"unknown optional tool bundles ignored: {sorted(unknown)}; "
            f"known: {sorted(OPTIONAL_BUNDLES)}"
        )
    ]


def optional_modules(env: Mapping[str, str]) -> tuple[str, ...]:
    """Return selected module names in deterministic registration order."""
    enabled = enabled_bundles(env)
    modules: list[str] = []
    for bundle, bundle_modules in OPTIONAL_BUNDLES.items():
        if bundle not in enabled:
            continue
        for module_name in bundle_modules:
            if module_name not in modules:
                modules.append(module_name)
    return tuple(modules)


def import_optional_modules(env: Mapping[str, str]) -> list[str]:
    """Import selected tool modules and return their canonical module names.

    Import failures intentionally propagate: a known, explicitly requested
    bundle must not leave the server running with a partially registered surface.
    """
    imported: list[str] = []
    for module_name in optional_modules(env):
        importlib.import_module(module_name)
        imported.append(module_name)
    return imported


def optional_tool_names() -> frozenset[str]:
    """Return contract-declared optional names without importing tool modules."""
    return OPTIONAL_TOOL_NAMES
