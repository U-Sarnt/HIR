"""Builtin plugin registrations for the validated HIR workflow."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import hir.core.arp as arp_mod
import hir.core.fingerprint as fingerprint_mod
import hir.core.ping as ping_mod
import hir.core.traceroute as traceroute_mod
import hir.core.vendor as vendor_mod
import hir.output.console as console_mod
import hir.output.html as html_mod
import hir.output.json as json_mod
from hir import __version__
from hir.core.models import ArpScanResult, PingResult, TracerouteResult
from hir.plugins.contracts import (
    AcquisitionProvider,
    OSFingerprintProvider,
    OutputHandler,
    OutputRequest,
    PluginMetadata,
    ReportLoader,
    VendorResolver,
)
from hir.plugins.registry import PluginRegistry


class BuiltinAcquisitionPlugin:
    """Builtin providers for the validated command/report workflow."""

    metadata = PluginMetadata(
        name="hir.builtin.acquisition",
        version=__version__,
        description="Builtin ping, traceroute, and ARP acquisition providers.",
        builtin=True,
    )

    def register(self, registry: PluginRegistry) -> None:
        registry.register_acquisition_provider(
            AcquisitionProvider(
                name="ping",
                report_type="ping",
                runner=_run_ping,
                description="Runs the validated system ping workflow.",
            )
        )
        registry.register_acquisition_provider(
            AcquisitionProvider(
                name="traceroute",
                report_type="traceroute",
                runner=_run_traceroute,
                description="Runs the validated system traceroute workflow.",
            )
        )
        registry.register_acquisition_provider(
            AcquisitionProvider(
                name="arp-scan",
                report_type="arp-scan",
                runner=_run_arp_scan,
                description="Runs the validated Scapy-based ARP discovery workflow.",
            )
        )


class BuiltinOutputPlugin:
    """Builtin output and persisted-report loading capabilities."""

    metadata = PluginMetadata(
        name="hir.builtin.output",
        version=__version__,
        description="Builtin console, JSON, and HTML output handlers plus JSON report loading.",
        builtin=True,
    )

    def register(self, registry: PluginRegistry) -> None:
        registry.register_output_handler(
            OutputHandler(
                name="builtin.console.ping",
                output_format="console",
                report_types=("ping",),
                destination="stdout",
                handler=_render_ping_console,
                description="Console renderer for ping reports.",
            )
        )
        registry.register_output_handler(
            OutputHandler(
                name="builtin.console.traceroute",
                output_format="console",
                report_types=("traceroute",),
                destination="stdout",
                handler=_render_traceroute_console,
                description="Console renderer for traceroute reports.",
            )
        )
        registry.register_output_handler(
            OutputHandler(
                name="builtin.console.arp-scan",
                output_format="console",
                report_types=("arp-scan",),
                destination="stdout",
                handler=_render_arp_console,
                description="Console renderer for ARP scan reports.",
            )
        )
        registry.register_output_handler(
            OutputHandler(
                name="builtin.file.json",
                output_format="json",
                report_types=("ping", "traceroute", "arp-scan"),
                destination="file",
                handler=_export_json,
                description="JSON exporter for validated report documents.",
                file_suffix=".json",
                default_directory="results/json",
            )
        )
        registry.register_output_handler(
            OutputHandler(
                name="builtin.file.html",
                output_format="html",
                report_types=("traceroute", "arp-scan"),
                destination="file",
                handler=_export_html,
                description="HTML exporter for traceroute and ARP reports.",
                file_suffix=".html",
                default_directory="results/html",
            )
        )
        registry.register_report_loader(
            ReportLoader(
                name="builtin.report-loader.json",
                suffixes=(".json",),
                supported_report_types=("traceroute", "arp-scan"),
                loader=_load_json_report,
                description="Loads supported JSON reports for report-export.",
            )
        )


class BuiltinEnrichmentPlugin:
    """Builtin enrichment providers for ARP post-processing."""

    metadata = PluginMetadata(
        name="hir.builtin.enrichment",
        version=__version__,
        description="Builtin MAC vendor lookup and heuristic OS fingerprint providers.",
        builtin=True,
    )

    def register(self, registry: PluginRegistry) -> None:
        registry.register_vendor_resolver(
            VendorResolver(
                name="oui-database",
                resolver=_resolve_oui_vendor,
                description="Looks up the first three MAC bytes in the packaged OUI database.",
                priority=10,
            )
        )
        registry.register_os_fingerprint_provider(
            OSFingerprintProvider(
                name="nmap",
                detector=_fingerprint_with_nmap,
                description="Uses nmap OS guessing when available.",
                priority=10,
            )
        )
        registry.register_os_fingerprint_provider(
            OSFingerprintProvider(
                name="scapy",
                detector=_fingerprint_with_scapy,
                description="Uses lightweight Scapy probes for heuristic OS guesses.",
                priority=20,
            )
        )
        registry.register_os_fingerprint_provider(
            OSFingerprintProvider(
                name="ttl",
                detector=_fingerprint_with_ttl,
                description="Infers a coarse OS family from a ping TTL value.",
                priority=30,
            )
        )
        registry.register_os_fingerprint_provider(
            OSFingerprintProvider(
                name="snmp",
                detector=_fingerprint_with_snmp,
                description="Uses SNMP sysDescr hints when they are reachable.",
                priority=40,
            )
        )


def iter_builtin_plugins() -> tuple[object, ...]:
    """Return the builtin plugins that form the current validated runtime."""
    return (
        BuiltinAcquisitionPlugin(),
        BuiltinOutputPlugin(),
        BuiltinEnrichmentPlugin(),
    )


def _run_ping(host: str, count: int = 4, timeout: int = 2) -> PingResult:
    return ping_mod.run_ping(host, count=count, timeout=timeout)


def _run_traceroute(host: str, max_hops: int = 30, timeout: int = 2) -> TracerouteResult:
    return traceroute_mod.run_traceroute(host, max_hops=max_hops, timeout=timeout)


def _run_arp_scan(subnet: str, timeout: int = 1) -> ArpScanResult:
    return arp_mod.run_arp_scan(subnet, timeout=timeout)


def _render_ping_console(report: object, _request: OutputRequest) -> str:
    return console_mod.render_ping_console(cast(PingResult, report))


def _render_traceroute_console(report: object, _request: OutputRequest) -> str:
    return console_mod.render_traceroute_console(cast(TracerouteResult, report))


def _render_arp_console(report: object, _request: OutputRequest) -> str:
    return console_mod.render_arp_console(cast(ArpScanResult, report))


def _export_json(report: object, request: OutputRequest) -> str:
    directory = request.output_dir if request.output_dir is not None else "results/json"
    return json_mod.dump_json(
        cast(json_mod.SerializableReport, report),
        base_filename=request.base_filename,
        directory=directory,
    )


def _export_html(report: object, request: OutputRequest) -> str:
    directory = request.output_dir if request.output_dir is not None else "results/html"
    return html_mod.render_html(
        cast(html_mod.HtmlReport, report),
        base_filename=request.base_filename,
        directory=directory,
    )


def _load_json_report(report_path: str | Path) -> object:
    return json_mod.load_report(report_path)


def _resolve_oui_vendor(mac: str) -> str:
    return vendor_mod.lookup_vendor_from_oui(mac)


def _fingerprint_with_nmap(ip: str) -> str:
    return fingerprint_mod.os_fingerprint_nmap(ip)


def _fingerprint_with_scapy(ip: str) -> str:
    return fingerprint_mod.os_fingerprint_scapy(ip)


def _fingerprint_with_ttl(ip: str) -> str:
    return fingerprint_mod.os_fingerprint_ttl(ip)


def _fingerprint_with_snmp(ip: str) -> str:
    return fingerprint_mod.os_fingerprint_snmp(ip)
