"""Stable output-contract helpers shared by JSON and HTML backends."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

from hir.core.errors import ParseError, ReportExportError
from hir.core.models import ArpScanResult, PingResult, SupportedExportReport, TracerouteResult

REPORT_DOCUMENT_SCHEMA = "hir.report"
REPORT_DOCUMENT_SCHEMA_VERSION = 1

ReportType = Literal["ping", "traceroute", "arp-scan"]
JsonReport = PingResult | TracerouteResult | ArpScanResult

_REPORT_DOCUMENT_KEYS = {"schema", "schema_version", "report_type", "report"}


def build_report_document(report: JsonReport) -> dict[str, Any]:
    """Return the stable versioned document for a report payload."""
    return {
        "schema": REPORT_DOCUMENT_SCHEMA,
        "schema_version": REPORT_DOCUMENT_SCHEMA_VERSION,
        "report_type": report_type_for_report(report),
        "report": report.to_dict(),
    }


def coerce_report_document(data: Mapping[str, Any] | JsonReport) -> dict[str, Any]:
    """Normalize a raw payload or typed report into the current document shape."""
    if isinstance(data, (PingResult, TracerouteResult, ArpScanResult)):
        return build_report_document(data)
    if isinstance(data, Mapping):
        return build_report_document(parse_report_document(data))
    raise ReportExportError(
        "JSON export requires a ping, traceroute, or arp-scan report payload."
    )


def parse_report_document(payload: Mapping[str, Any]) -> JsonReport:
    """Parse a versioned or legacy report document into its typed model."""
    report_type, report_payload = unpack_report_document(payload)
    return _parse_report_payload(report_type, report_payload)


def parse_supported_report_document(payload: Mapping[str, Any]) -> SupportedExportReport:
    """Parse a supported report document for HTML export."""
    report_type, report_payload = unpack_report_document(payload)
    if report_type == "traceroute":
        return TracerouteResult.from_payload(report_payload)
    if report_type == "arp-scan":
        return ArpScanResult.from_payload(report_payload)
    raise ReportExportError(
        "Unsupported report type. report-export only accepts traceroute or arp-scan JSON exports."
    )


def unpack_report_document(payload: Mapping[str, Any]) -> tuple[ReportType, dict[str, Any]]:
    """Return the report type and raw payload from a versioned or legacy document."""
    if _looks_like_report_document(payload):
        schema = payload.get("schema")
        if schema != REPORT_DOCUMENT_SCHEMA:
            raise ParseError(f"Unsupported report schema: {schema!r}.")

        schema_version = payload.get("schema_version")
        if schema_version != REPORT_DOCUMENT_SCHEMA_VERSION:
            raise ParseError(
                f"Unsupported report schema version: {schema_version!r}. "
                f"Expected {REPORT_DOCUMENT_SCHEMA_VERSION}."
            )

        report_type = payload.get("report_type")
        if report_type not in ("ping", "traceroute", "arp-scan"):
            raise ReportExportError(
                f"Unsupported report type: {report_type!r}. "
                "Expected 'ping', 'traceroute', or 'arp-scan'."
            )

        report_payload = payload.get("report")
        if not isinstance(report_payload, Mapping):
            raise ParseError("Report documents must contain a 'report' object.")

        return report_type, dict(report_payload)

    inferred_type = _infer_report_type(payload)
    return inferred_type, dict(payload)


def _parse_report_payload(report_type: ReportType, payload: Mapping[str, Any]) -> JsonReport:
    if report_type == "ping":
        return PingResult.from_payload(payload)
    if report_type == "traceroute":
        return TracerouteResult.from_payload(payload)
    if report_type == "arp-scan":
        return ArpScanResult.from_payload(payload)

    raise ReportExportError(
        f"Unsupported report type: {report_type!r}. "
        "Expected 'ping', 'traceroute', or 'arp-scan'."
    )


def report_type_for_report(report: JsonReport) -> ReportType:
    if isinstance(report, PingResult):
        return "ping"
    if isinstance(report, TracerouteResult):
        return "traceroute"
    return "arp-scan"


def _infer_report_type(payload: Mapping[str, Any]) -> ReportType:
    if "host" in payload and "count" in payload and "rtt_ms" in payload:
        return "ping"
    if "host" in payload and "hops" in payload:
        return "traceroute"
    if "subnet" in payload and "devices" in payload:
        return "arp-scan"

    raise ReportExportError(
        "Unsupported report type. Expected a ping, traceroute, or arp-scan report payload."
    )


def _looks_like_report_document(payload: Mapping[str, Any]) -> bool:
    return any(key in payload for key in _REPORT_DOCUMENT_KEYS)
