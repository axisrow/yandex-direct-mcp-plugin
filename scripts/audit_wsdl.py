#!/usr/bin/env python3
"""Audit the MCP public Direct v5 contract against live Yandex Direct WSDL.

The plugin intentionally exposes a thin MCP layer over the ``direct`` CLI. This
script validates the WSDL-backed part of ``server.contract`` without touching
the reports API, v4 Live tools, CLI helpers, or plugin-only tools.
"""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, Sequence
from xml.etree import ElementTree as ET

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.contract import PUBLIC_CONTRACT, TRANSPORT_BLOCKED_OPERATIONS  # noqa: E402

WSDL_BASE_URL = "https://api.direct.yandex.com/v5"
WSDL_NS = "http://schemas.xmlsoap.org/wsdl/"

# ``DIRECT_API_SERVICE_METHODS`` uses the public MCP/direct-cli service names.
# A few official WSDL endpoints are named differently.
WSDL_ENDPOINTS_BY_SERVICE: dict[str, str] = {
    "dynamicads": "dynamictextadtargets",
    "retargeting": "retargetinglists",
}

# Legacy names can still appear in TRANSPORT_BLOCKED_OPERATIONS because that
# mapping also documents removed public aliases.
BLOCKED_SERVICE_ALIASES: dict[str, str] = {
    "dynamic_ads": "dynamicads",
    "negative_keywords": "negativekeywords",
}


class WSDLFetchError(RuntimeError):
    """Raised when a WSDL endpoint cannot be fetched or parsed."""


@dataclass(frozen=True)
class BlockedOperation:
    public_name: str
    service: str
    method: str | None


@dataclass(frozen=True)
class AuditResult:
    checked_services: frozenset[str]
    missing_services: dict[str, frozenset[str]] = field(default_factory=dict)
    missing_methods: dict[str, frozenset[str]] = field(default_factory=dict)
    extra_contract_methods: dict[str, frozenset[str]] = field(default_factory=dict)
    stale_blocked_operations: frozenset[str] = field(default_factory=frozenset)
    unchecked_blocked_operations: frozenset[str] = field(default_factory=frozenset)
    fetch_errors: dict[str, str] = field(default_factory=dict)

    @property
    def has_contract_drift(self) -> bool:
        return bool(
            self.missing_services or self.missing_methods or self.extra_contract_methods
        )

    @property
    def exit_code(self) -> int:
        if self.fetch_errors:
            return 2
        if self.has_contract_drift:
            return 1
        return 0


def method_to_wsdl_name(method: str) -> str:
    """Convert raw blocked-operation snake_case method names to WSDL camelCase."""
    parts = method.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def service_to_wsdl_endpoint(service: str) -> str:
    """Return the official WSDL endpoint name for a contract service name."""
    return WSDL_ENDPOINTS_BY_SERVICE.get(service, service)


def wsdl_url_for_service(service: str, base_url: str = WSDL_BASE_URL) -> str:
    endpoint = service_to_wsdl_endpoint(service)
    return f"{base_url.rstrip('/')}/{endpoint}?wsdl"


def parse_wsdl_operations(content: bytes) -> frozenset[str]:
    """Extract operation names from all WSDL portType nodes."""
    root = ET.fromstring(content)
    operations: set[str] = set()
    for port_type in root.findall(f".//{{{WSDL_NS}}}portType"):
        for operation in port_type.findall(f"{{{WSDL_NS}}}operation"):
            name = operation.attrib.get("name")
            if name:
                operations.add(name)
    return frozenset(operations)


def fetch_wsdl_operations(url: str, timeout: float) -> frozenset[str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return parse_wsdl_operations(response.read())
    except urllib.error.HTTPError as exc:
        raise WSDLFetchError(f"HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise WSDLFetchError(str(exc.reason)) from exc
    except (TimeoutError, OSError) as exc:
        # ``urllib`` only wraps connect-phase failures in ``URLError``. A read
        # timeout that stalls in the middle of ``response.read()`` surfaces as
        # a bare ``TimeoutError`` / ``socket.timeout`` (alias of
        # ``TimeoutError`` since Python 3.10), and connection resets / broken
        # pipes during the body transfer come through as other ``OSError``
        # subclasses. Without this clause one slow service would abort the
        # whole live audit instead of being recorded as an inconclusive fetch.
        raise WSDLFetchError(f"network error: {exc}") from exc
    except ET.ParseError as exc:
        raise WSDLFetchError(f"XML parse error: {exc}") from exc


def auditable_contract_methods(
    contract_methods: Mapping[str, Sequence[str]] | None = None,
) -> dict[str, frozenset[str]]:
    """Return only Direct v5 WSDL-backed service methods in WSDL naming."""
    if contract_methods is not None:
        return {
            service: frozenset(method_to_wsdl_name(method) for method in methods)
            for service, methods in contract_methods.items()
        }

    methods_by_service: dict[str, set[str]] = {}
    for tool in PUBLIC_CONTRACT:
        if tool.authority != "wsdl" or tool.cli_service is None:
            continue
        canonical = tool.tapi_canonical
        if canonical is None:
            continue
        methods_by_service.setdefault(tool.cli_service, set()).add(canonical)

    return {
        service: frozenset(methods)
        for service, methods in sorted(methods_by_service.items())
    }


def _resolve_blocked_operation(
    public_name: str,
    known_services: frozenset[str],
) -> BlockedOperation:
    if public_name.endswith("_*"):
        raw_service = public_name[:-2]
        service = BLOCKED_SERVICE_ALIASES.get(raw_service, raw_service)
        return BlockedOperation(public_name=public_name, service=service, method=None)

    candidates = sorted(
        set(known_services) | set(BLOCKED_SERVICE_ALIASES),
        key=len,
        reverse=True,
    )
    for candidate in candidates:
        prefix = f"{candidate}_"
        if public_name.startswith(prefix):
            service = BLOCKED_SERVICE_ALIASES.get(candidate, candidate)
            raw_method = public_name[len(prefix) :]
            return BlockedOperation(
                public_name=public_name,
                service=service,
                method=method_to_wsdl_name(raw_method),
            )

    return BlockedOperation(public_name=public_name, service=public_name, method=None)


def blocked_methods_by_service(
    blocked_operations: Mapping[str, str],
    known_services: frozenset[str],
) -> tuple[dict[str, frozenset[str]], frozenset[str]]:
    blocked: dict[str, set[str]] = {}
    unchecked: set[str] = set()

    for public_name in blocked_operations:
        operation = _resolve_blocked_operation(public_name, known_services)
        if operation.method is None:
            unchecked.add(public_name)
            continue
        blocked.setdefault(operation.service, set()).add(operation.method)

    return (
        {service: frozenset(methods) for service, methods in blocked.items()},
        frozenset(unchecked),
    )


def compare_wsdl_to_contract(
    wsdl_methods: Mapping[str, frozenset[str]],
    contract_methods: Mapping[str, Sequence[str]] | None = None,
    blocked_operations: Mapping[str, str] = TRANSPORT_BLOCKED_OPERATIONS,
) -> AuditResult:
    declared = auditable_contract_methods(contract_methods)
    declared_services = frozenset(declared)
    wsdl_services = frozenset(wsdl_methods)
    known_services = (
        declared_services | wsdl_services | frozenset(WSDL_ENDPOINTS_BY_SERVICE)
    )
    blocked, unchecked_blocked = blocked_methods_by_service(
        blocked_operations, known_services
    )

    missing_services = {
        service: frozenset(wsdl_methods[service])
        for service in sorted(wsdl_services - declared_services)
    }

    missing_methods: dict[str, frozenset[str]] = {}
    extra_contract_methods: dict[str, frozenset[str]] = {}

    for service in sorted(declared_services & wsdl_services):
        blocked_methods = blocked.get(service, frozenset())
        missing = wsdl_methods[service] - declared[service] - blocked_methods
        extra = declared[service] - wsdl_methods[service]
        if missing:
            missing_methods[service] = frozenset(missing)
        if extra:
            extra_contract_methods[service] = frozenset(extra)

    stale_blocked: set[str] = set()
    for public_name in blocked_operations:
        operation = _resolve_blocked_operation(public_name, known_services)
        if operation.method is None:
            continue
        service_declared = declared.get(operation.service, frozenset())
        service_wsdl = wsdl_methods.get(operation.service)
        if operation.method in service_declared:
            stale_blocked.add(public_name)
        elif service_wsdl is not None and operation.method not in service_wsdl:
            stale_blocked.add(public_name)

    return AuditResult(
        checked_services=frozenset(wsdl_services & declared_services),
        missing_services=missing_services,
        missing_methods=missing_methods,
        extra_contract_methods=extra_contract_methods,
        stale_blocked_operations=frozenset(stale_blocked),
        unchecked_blocked_operations=unchecked_blocked,
    )


def run_live_audit(
    *,
    timeout: float,
    services: frozenset[str] | None = None,
    base_url: str = WSDL_BASE_URL,
    fetcher: Callable[[str, float], frozenset[str]] = fetch_wsdl_operations,
) -> AuditResult:
    declared = auditable_contract_methods()
    service_names = services or frozenset(declared)

    wsdl_methods: dict[str, frozenset[str]] = {}
    fetch_errors: dict[str, str] = {}

    for service in sorted(service_names):
        if service not in declared:
            fetch_errors[service] = (
                "service is not a WSDL-backed Direct v5 contract service"
            )
            continue
        url = wsdl_url_for_service(service, base_url)
        try:
            wsdl_methods[service] = fetcher(url, timeout)
        except WSDLFetchError as exc:
            fetch_errors[service] = f"{url}: {exc}"

    result = compare_wsdl_to_contract(wsdl_methods)
    return AuditResult(
        checked_services=result.checked_services,
        missing_services=result.missing_services,
        missing_methods=result.missing_methods,
        extra_contract_methods=result.extra_contract_methods,
        stale_blocked_operations=result.stale_blocked_operations,
        unchecked_blocked_operations=result.unchecked_blocked_operations,
        fetch_errors=fetch_errors,
    )


def _format_method_map(items: Mapping[str, frozenset[str]]) -> list[str]:
    lines: list[str] = []
    for service, methods in sorted(items.items()):
        method_list = "`, `".join(sorted(methods))
        lines.append(f"- `{service}`: `{method_list}`")
    return lines


def format_report(result: AuditResult) -> str:
    lines = [
        "# Yandex Direct WSDL Audit",
        "",
        f"Checked WSDL services: {len(result.checked_services)}",
    ]

    if result.fetch_errors:
        lines.extend(["", "## Inconclusive WSDL Fetches"])
        for service, error in sorted(result.fetch_errors.items()):
            lines.append(f"- `{service}`: {error}")

    if (
        result.missing_services
        or result.missing_methods
        or result.extra_contract_methods
    ):
        lines.extend(["", "## Contract Drift"])
        if result.missing_services:
            lines.append("")
            lines.append("Missing services in DIRECT_API_SERVICE_METHODS:")
            lines.extend(_format_method_map(result.missing_services))
        if result.missing_methods:
            lines.append("")
            lines.append("Missing methods in DIRECT_API_SERVICE_METHODS:")
            lines.extend(_format_method_map(result.missing_methods))
        if result.extra_contract_methods:
            lines.append("")
            lines.append("Contract methods absent from live WSDL:")
            lines.extend(_format_method_map(result.extra_contract_methods))

    if result.stale_blocked_operations or result.unchecked_blocked_operations:
        lines.extend(["", "## Warnings"])
        if result.stale_blocked_operations:
            lines.append("")
            lines.append("Stale TRANSPORT_BLOCKED_OPERATIONS entries:")
            for operation in sorted(result.stale_blocked_operations):
                lines.append(f"- `{operation}`")
        if result.unchecked_blocked_operations:
            lines.append("")
            lines.append("Unchecked wildcard/non-service blocked entries:")
            for operation in sorted(result.unchecked_blocked_operations):
                lines.append(f"- `{operation}`")

    has_warnings = bool(
        result.stale_blocked_operations or result.unchecked_blocked_operations
    )
    if result.exit_code == 0 and has_warnings:
        lines.extend(["", "Result: OK WITH WARNINGS"])
    elif result.exit_code == 0:
        lines.extend(["", "Result: OK"])
    elif result.exit_code == 1:
        lines.extend(["", "Result: CONTRACT DRIFT"])
    else:
        lines.extend(["", "Result: INCONCLUSIVE"])

    return "\n".join(lines)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="WSDL fetch timeout in seconds.",
    )
    parser.add_argument(
        "--service",
        action="append",
        dest="services",
        help="Limit the audit to one contract service; can be repeated.",
    )
    parser.add_argument(
        "--base-url",
        default=WSDL_BASE_URL,
        help="Base URL for v5 WSDL endpoints.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    services = frozenset(args.services) if args.services else None
    result = run_live_audit(
        timeout=args.timeout,
        services=services,
        base_url=args.base_url,
    )
    print(format_report(result))
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
