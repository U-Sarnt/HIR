"""HTML report rendering helpers."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape

from hir.core.errors import ReportExportError
from hir.core.models import ArpScanResult, TracerouteResult, parse_supported_report_payload
from hir.output.files import build_output_path, finalize_output_path

HtmlReport = Mapping[str, Any] | TracerouteResult | ArpScanResult


def render_html(
    data: HtmlReport,
    base_filename: str | None = None,
    directory: str | Path = "results/html",
) -> str:
    """Render a supported traceroute or ARP report to HTML."""
    report = _coerce_html_report(data)
    out_path = build_output_path(
        directory,
        base_filename=base_filename,
        suffix=".html",
        default_base_filename="report",
    )

    env = _create_template_environment()
    template = env.get_template(_select_template_name(report))
    rendered = template.render(**_build_template_context(report))

    out_path.write_text(rendered, encoding="utf-8")
    finalize_output_path(out_path)
    return str(out_path)


def _create_template_environment() -> Environment:
    return Environment(
        loader=PackageLoader("hir.output", "templates"),
        autoescape=select_autoescape(["html"]),
    )


def _select_template_name(data: TracerouteResult | ArpScanResult) -> str:
    if isinstance(data, TracerouteResult):
        return "traceroute_report.html.j2"
    return "arp_report.html.j2"


def _coerce_html_report(data: HtmlReport) -> TracerouteResult | ArpScanResult:
    if isinstance(data, (TracerouteResult, ArpScanResult)):
        return data
    if isinstance(data, Mapping):
        return parse_supported_report_payload(dict(data))
    raise ReportExportError("HTML export requires a traceroute or ARP report.")


def _build_template_context(data: TracerouteResult | ArpScanResult) -> dict[str, Any]:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(data, TracerouteResult):
        return {
            "host": data.host,
            "hops": [hop.to_tuple() for hop in data.hops],
            "timestamp": timestamp,
        }

    return {
        "subnet": data.subnet,
        "devices": [device.to_dict() for device in data.devices],
        "timestamp": timestamp,
        "os_note": data.os_note,
    }
