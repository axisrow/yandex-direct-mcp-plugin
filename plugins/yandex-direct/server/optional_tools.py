"""Bundle import gate for tool modules outside the base server/main.py imports.

FastMCP registers decorated tools eagerly while their modules are imported.  To
keep a module's tool schemas together, module selection must therefore happen
before import rather than by removing tools afterwards.

All known bundles load by default (default-on decision after #312): the browser
surface works without YANDEX_DIRECT_OPTIONAL_TOOLS, and users opt out through
the tool-surface config instead (YANDEX_DIRECT_DISABLED_GROUPS=browser or
YANDEX_DIRECT_DISABLED_TOOLS). The env variable remains supported as an
explicit narrow-down override. A bundle module that fails to import degrades
softly under the default (tool absent, server and tools/list stay alive); an
explicitly requested bundle still fails closed, as it did when it was opt-in.
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
        "server.tools.adrestrictions",
        "server.tools.playwright",
    ),
    "trackingparams": ("server.tools.trackingparams",),
}


def _configured_bundles(env: Mapping[str, str]) -> frozenset[str]:
    raw = env.get(ENV_OPTIONAL_TOOLS, "")
    return frozenset(item.strip().lower() for item in raw.split(",") if item.strip())


def enabled_bundles(env: Mapping[str, str]) -> frozenset[str]:
    """Return bundles enabled by ``env``.

    An unset/empty ``env`` enables every known bundle (default-on). A non-empty
    ``env`` is an explicit override: ``all`` expands every bundle, anything else
    narrows the loaded bundles to the known, named ones.
    """
    configured = _configured_bundles(env)
    if "all" in configured:
        return frozenset(OPTIONAL_BUNDLES)
    if not configured:
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

    Fail-safe under the default-on start: a bundle module whose extra is
    missing degrades softly (module skipped, its tools absent, server and
    tools/list alive). An explicitly configured env keeps the original
    fail-closed contract: a known, explicitly requested bundle must not leave
    the server running with a partially registered surface.
    """
    explicit = bool(_configured_bundles(env))
    imported: list[str] = []
    for module_name in optional_modules(env):
        try:
            importlib.import_module(module_name)
        except ImportError:
            if explicit:
                raise
            # Skip only the broken bundle module; sibling bundles stay alive.
            continue
        imported.append(module_name)
    return imported


def optional_tool_names() -> frozenset[str]:
    """Return contract-declared optional names without importing tool modules."""
    return OPTIONAL_TOOL_NAMES
