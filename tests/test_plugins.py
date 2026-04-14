from __future__ import annotations

import json
from pathlib import Path

import pytest

import hir.core.fingerprint as fingerprint_mod
import hir.core.vendor as vendor_mod
import hir.plugins.discovery as discovery_mod
import hir.plugins.runtime as runtime_mod
from hir.core.errors import PluginCompatibilityError, PluginDiscoveryError, PluginLookupError
from hir.core.models import UNKNOWN_OS
from hir.plugins.contracts import (
    CapabilityKind,
    OSFingerprintProvider,
    OutputRequest,
    PluginMetadata,
    VendorResolver,
)
from hir.plugins.registry import PluginRegistry


class _VendorPlugin:
    metadata = PluginMetadata(name="test.vendor", version="1.0.0")

    def register(self, registry: PluginRegistry) -> None:
        registry.register_vendor_resolver(
            VendorResolver(
                name="test-vendor",
                resolver=lambda _mac: "Plugin Vendor",
                description="Test-only resolver.",
                priority=1,
            )
        )


class _BrokenPlugin:
    metadata = PluginMetadata(name="test.broken", version="1.0.0", api_version=99)

    def register(self, registry: PluginRegistry) -> None:
        registry.register_vendor_resolver(
            VendorResolver(name="broken", resolver=lambda _mac: "broken")
        )


class _FingerprintPlugin:
    metadata = PluginMetadata(name="test.fingerprint", version="1.0.0")

    def register(self, registry: PluginRegistry) -> None:
        registry.register_os_fingerprint_provider(
            OSFingerprintProvider(
                name="always-unknown",
                detector=lambda _ip: UNKNOWN_OS,
                priority=10,
            )
        )
        registry.register_os_fingerprint_provider(
            OSFingerprintProvider(
                name="plugin-detector",
                detector=lambda _ip: "PluginOS",
                priority=20,
            )
        )


class _FakeEntryPoint:
    def __init__(self, name: str, loaded: object) -> None:
        self.name = name
        self._loaded = loaded

    def load(self) -> object:
        return self._loaded


def test_builtin_discovery_registers_expected_plugins_and_capabilities() -> None:
    result = discovery_mod.discover_plugins(include_entry_points=False)

    assert tuple(metadata.name for metadata in result.registry.list_plugins()) == (
        "hir.builtin.acquisition",
        "hir.builtin.enrichment",
        "hir.builtin.output",
    )
    assert result.registry.get_output_formats("ping") == ("console", "json")
    assert result.registry.get_output_formats("traceroute") == ("console", "json", "html")

    fingerprint_capabilities = {
        capability.name
        for capability in result.registry.list_capabilities()
        if capability.kind == CapabilityKind.OS_FINGERPRINT
    }
    assert fingerprint_capabilities == {"nmap", "scapy", "snmp", "ttl"}


def test_discovery_loads_external_entry_point_plugin(monkeypatch) -> None:
    monkeypatch.setattr(
        discovery_mod,
        "_iter_plugin_entry_points",
        lambda: (_FakeEntryPoint("test-vendor", _VendorPlugin()),),
    )

    result = discovery_mod.discover_plugins()

    assert result.failures == ()
    assert any(metadata.name == "test.vendor" for metadata in result.registry.list_plugins())
    assert any(
        capability.name == "test-vendor" for capability in result.registry.list_capabilities()
    )


def test_discovery_collects_invalid_entry_point_failures_when_not_strict(monkeypatch) -> None:
    monkeypatch.setattr(
        discovery_mod,
        "_iter_plugin_entry_points",
        lambda: (_FakeEntryPoint("broken-plugin", object()),),
    )

    result = discovery_mod.discover_plugins()

    assert len(result.failures) == 1
    assert result.failures[0].plugin_name == "broken-plugin"
    assert "valid HIR plugin object" in result.failures[0].message


def test_discovery_raises_for_invalid_entry_point_in_strict_mode(monkeypatch) -> None:
    monkeypatch.setattr(
        discovery_mod,
        "_iter_plugin_entry_points",
        lambda: (_FakeEntryPoint("broken-plugin", object()),),
    )

    with pytest.raises(PluginDiscoveryError, match="broken-plugin"):
        discovery_mod.discover_plugins(strict=True)


def test_registry_rejects_plugins_with_incompatible_api_version() -> None:
    with pytest.raises(PluginCompatibilityError, match="test.broken"):
        PluginRegistry().register_plugin(_BrokenPlugin())


def test_builtin_registry_loads_and_exports_reports(tmp_path: Path) -> None:
    result = discovery_mod.discover_plugins(include_entry_points=False)
    report_path = tmp_path / "traceroute.json"
    report_path.write_text(
        json.dumps(
            {
                "schema": "hir.report",
                "schema_version": 1,
                "report_type": "traceroute",
                "report": {
                    "host": "example.com",
                    "hops": [{"hop": 1, "ip": "192.168.1.1", "rtt_ms": 1.23}],
                },
            }
        ),
        encoding="utf-8",
    )

    report = result.registry.load_report(report_path)
    handler = result.registry.get_output_handler("html", "traceroute")
    html_path = handler.handler(
        report,
        OutputRequest(base_filename="trace", output_dir=tmp_path),
    )

    assert html_path is not None
    assert Path(html_path).name == "trace_01.html"
    assert "example.com" in Path(html_path).read_text(encoding="utf-8")


def test_registry_fails_clearly_for_unsupported_report_suffix(tmp_path: Path) -> None:
    result = discovery_mod.discover_plugins(include_entry_points=False)
    report_path = tmp_path / "report.yaml"
    report_path.write_text("host: example.com\n", encoding="utf-8")

    with pytest.raises(PluginLookupError, match="No report loader is registered"):
        result.registry.load_report(report_path)


def test_vendor_lookup_uses_runtime_registry(monkeypatch) -> None:
    registry = PluginRegistry()
    registry.register_plugin(_VendorPlugin())
    monkeypatch.setattr(runtime_mod, "get_runtime_registry", lambda: registry)

    assert vendor_mod.get_vendor_from_mac("aa:bb:cc:dd:ee:ff") == "Plugin Vendor"


def test_hybrid_os_fingerprint_uses_runtime_registry(monkeypatch) -> None:
    registry = PluginRegistry()
    registry.register_plugin(_FingerprintPlugin())
    monkeypatch.setattr(runtime_mod, "get_runtime_registry", lambda: registry)

    assert fingerprint_mod.hybrid_os_fingerprint("192.0.2.10") == "PluginOS"
