"""Tests for the live WSDL contract audit helper."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit_wsdl.py"
spec = importlib.util.spec_from_file_location("audit_wsdl", MODULE_PATH)
assert spec is not None
audit_wsdl = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = audit_wsdl
spec.loader.exec_module(audit_wsdl)


def test_method_to_wsdl_name_normalizes_snake_case_methods():
    assert audit_wsdl.method_to_wsdl_name("set_auto") == "setAuto"
    assert audit_wsdl.method_to_wsdl_name("get_geo_regions") == "getGeoRegions"
    assert (
        audit_wsdl.method_to_wsdl_name("add_passport_organization_member")
        == "addPassportOrganizationMember"
    )


def test_parse_wsdl_operations_extracts_port_type_operations():
    xml = b"""
    <definitions xmlns="http://schemas.xmlsoap.org/wsdl/">
      <portType name="StrategiesServicePortType">
        <operation name="add" />
        <operation name="archive" />
        <operation name="get" />
      </portType>
      <binding name="IgnoredBinding">
        <operation name="notFromPortType" />
      </binding>
    </definitions>
    """

    assert audit_wsdl.parse_wsdl_operations(xml) == frozenset({"add", "archive", "get"})


def test_compare_reports_missing_service_method_and_stale_blocked_operation():
    wsdl_methods = {
        "campaigns": frozenset({"get", "add"}),
        "strategies": frozenset({"get", "add", "update", "archive", "unarchive"}),
        "bidmodifiers": frozenset({"get"}),
    }
    contract_methods = {
        "campaigns": ("get",),
        "bidmodifiers": ("get",),
        "reports": ("get",),
    }

    result = audit_wsdl.compare_wsdl_to_contract(
        wsdl_methods,
        contract_methods,
        {
            "campaigns_get": "already declared in the contract",
            "bidmodifiers_toggle": "operation no longer exists in live WSDL",
        },
    )

    assert result.exit_code == 1
    assert result.missing_services == {
        "strategies": frozenset({"get", "add", "update", "archive", "unarchive"})
    }
    assert result.missing_methods == {"campaigns": frozenset({"add"})}
    assert result.extra_contract_methods == {}
    assert result.stale_blocked_operations == frozenset(
        {"campaigns_get", "bidmodifiers_toggle"}
    )

    report = audit_wsdl.format_report(result)
    assert "Missing services in DIRECT_API_SERVICE_METHODS" in report
    assert "Missing methods in DIRECT_API_SERVICE_METHODS" in report
    assert "Stale TRANSPORT_BLOCKED_OPERATIONS entries" in report


def test_run_live_audit_excludes_reports_and_uses_wsdl_endpoint_aliases():
    fetched: list[str] = []

    def fake_fetcher(url: str, timeout: float) -> frozenset[str]:
        fetched.append(url)
        assert timeout == 3.0
        if url.endswith("/dynamictextadtargets?wsdl"):
            return frozenset({"get", "add", "delete", "suspend", "resume", "setBids"})
        if url.endswith("/retargetinglists?wsdl"):
            return frozenset({"get", "add", "update", "delete"})
        raise AssertionError(f"unexpected URL: {url}")

    result = audit_wsdl.run_live_audit(
        timeout=3.0,
        services=frozenset({"dynamicads", "retargeting"}),
        fetcher=fake_fetcher,
    )

    assert result.exit_code == 0
    assert fetched == [
        "https://api.direct.yandex.com/v5/dynamictextadtargets?wsdl",
        "https://api.direct.yandex.com/v5/retargetinglists?wsdl",
    ]


def test_run_live_audit_marks_non_wsdl_service_as_inconclusive():
    result = audit_wsdl.run_live_audit(timeout=3.0, services=frozenset({"reports"}))

    assert result.exit_code == 2
    assert result.fetch_errors == {
        "reports": "service is not a WSDL-backed Direct v5 contract service"
    }


def test_fetch_wsdl_operations_wraps_body_read_timeout():
    """A ``TimeoutError`` raised mid-read must be wrapped in WSDLFetchError.

    ``urllib`` only wraps connect-phase failures in ``URLError``; a stall
    inside ``response.read()`` surfaces a bare ``TimeoutError`` (which is
    also the alias ``socket.timeout`` on Python 3.10+). The fetcher must
    convert it into ``WSDLFetchError`` so ``run_live_audit`` records the
    service as an inconclusive fetch instead of aborting the whole run.
    """
    import urllib.request
    from unittest.mock import MagicMock, patch

    class _ReadTimeoutResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def read(self):
            raise TimeoutError("simulated body-read stall")

    with patch.object(
        urllib.request, "urlopen", MagicMock(return_value=_ReadTimeoutResponse())
    ):
        try:
            audit_wsdl.fetch_wsdl_operations("https://example.invalid/?wsdl", 1.0)
        except audit_wsdl.WSDLFetchError as exc:
            assert "network error" in str(exc)
        else:  # pragma: no cover — defensive
            raise AssertionError("WSDLFetchError was not raised")


def test_run_live_audit_continues_after_single_service_timeout():
    """One slow service must not abort the audit of the rest of the suite."""

    def flaky_fetcher(url: str, timeout: float) -> frozenset[str]:
        if "campaigns?wsdl" in url:
            raise audit_wsdl.WSDLFetchError("network error: timed out")
        return frozenset({"get"})

    contract_services = frozenset(audit_wsdl.auditable_contract_methods())
    sample_services = frozenset({"campaigns", "bidmodifiers"}) & contract_services

    result = audit_wsdl.run_live_audit(
        timeout=1.0,
        services=sample_services,
        fetcher=flaky_fetcher,
    )

    assert "campaigns" in result.fetch_errors
    assert "timed out" in result.fetch_errors["campaigns"]
    # The other service still made it through the run.
    assert "bidmodifiers" not in result.fetch_errors
    assert result.exit_code == 2  # inconclusive because of the fetch_error
