"""Typed core result models for the validated HIR workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from hir.core.errors import ParseError, ReportExportError

UNKNOWN_OS = "Desconocido"
INSUFFICIENT_OS_DATA = "Sin datos suficientes"
HEURISTIC_OS_NOTE = "El sistema operativo mostrado es una estimación heurística."
UNKNOWN_VENDOR = "Desconocido"


def format_os_guess(raw_os: str | None) -> str:
    """Return the validated user-facing wording for heuristic OS guesses."""
    if not raw_os or raw_os == UNKNOWN_OS:
        return INSUFFICIENT_OS_DATA
    return f"Posible {raw_os} (heurístico)"


@dataclass(frozen=True, slots=True)
class PingResult:
    """Structured ping outcome used by the CLI and export layers."""

    host: str
    count: int
    timeout: int
    rtt_ms: tuple[float, ...]
    received: int
    min_ms: float | None
    avg_ms: float | None
    max_ms: float | None

    @classmethod
    def from_rtt(cls, host: str, count: int, timeout: int, rtt_values: list[float]) -> "PingResult":
        """Build a result object from the parsed round-trip values."""
        values = tuple(rtt_values)
        received = len(values)

        if values:
            min_ms = min(values)
            avg_ms = sum(values) / received
            max_ms = max(values)
        else:
            min_ms = None
            avg_ms = None
            max_ms = None

        return cls(
            host=host,
            count=count,
            timeout=timeout,
            rtt_ms=values,
            received=received,
            min_ms=min_ms,
            avg_ms=avg_ms,
            max_ms=max_ms,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the stable JSON-serializable representation."""
        return {
            "host": self.host,
            "count": self.count,
            "timeout": self.timeout,
            "rtt_ms": list(self.rtt_ms),
            "received": self.received,
            "min_ms": self.min_ms,
            "avg_ms": self.avg_ms,
            "max_ms": self.max_ms,
        }


@dataclass(frozen=True, slots=True)
class TracerouteHop:
    """One parsed traceroute hop."""

    hop: int
    ip: str
    rtt_ms: float

    def to_tuple(self) -> tuple[int, str, float]:
        """Return the export-friendly tuple representation."""
        return (self.hop, self.ip, self.rtt_ms)

    @classmethod
    def from_payload(cls, payload: Any) -> "TracerouteHop":
        """Build a hop from a stored JSON-compatible sequence."""
        if not isinstance(payload, (list, tuple)) or len(payload) < 2:
            raise ParseError("Traceroute hops must be arrays like [hop, ip, rtt_ms].")

        try:
            hop = int(payload[0])
            ip = str(payload[1])
            rtt_ms = float(payload[2]) if len(payload) >= 3 else float("nan")
        except (TypeError, ValueError) as exc:
            raise ParseError("Traceroute hops must contain numeric hop and RTT values.") from exc

        return cls(hop=hop, ip=ip, rtt_ms=rtt_ms)


@dataclass(frozen=True, slots=True)
class TracerouteResult:
    """Structured traceroute outcome used by the CLI and export layers."""

    host: str
    max_hops: int | None
    timeout: int | None
    hops: tuple[TracerouteHop, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return the stable JSON-serializable representation."""
        return {
            "host": self.host,
            "max_hops": self.max_hops,
            "timeout": self.timeout,
            "hops": [hop.to_tuple() for hop in self.hops],
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "TracerouteResult":
        """Build a typed traceroute result from JSON-like data."""
        host = _require_string(payload, "host")
        raw_hops = payload.get("hops")
        if not isinstance(raw_hops, list):
            raise ParseError("Traceroute reports must contain a 'hops' array.")

        max_hops = _optional_int(payload.get("max_hops"), field_name="max_hops")
        timeout = _optional_int(payload.get("timeout"), field_name="timeout")
        hops = tuple(TracerouteHop.from_payload(item) for item in raw_hops)
        return cls(host=host, max_hops=max_hops, timeout=timeout, hops=hops)


@dataclass(frozen=True, slots=True)
class ArpHost:
    """One discovered ARP host and its best-effort enrichment."""

    ip: str
    mac: str
    vendor: str = UNKNOWN_VENDOR
    os: str = INSUFFICIENT_OS_DATA

    @classmethod
    def from_discovery(
        cls,
        ip: str,
        mac: str,
        vendor: str = UNKNOWN_VENDOR,
        raw_os: str | None = None,
    ) -> "ArpHost":
        """Build a host from low-level discovery data."""
        return cls(ip=ip, mac=mac, vendor=vendor, os=format_os_guess(raw_os))

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ArpHost":
        """Build a host from JSON-like data."""
        return cls(
            ip=_require_string(payload, "ip"),
            mac=_require_string(payload, "mac"),
            vendor=_optional_string(payload.get("vendor")) or UNKNOWN_VENDOR,
            os=_optional_string(payload.get("os")) or INSUFFICIENT_OS_DATA,
        )

    def to_dict(self) -> dict[str, str]:
        """Return the stable JSON-serializable representation."""
        return {
            "ip": self.ip,
            "mac": self.mac,
            "vendor": self.vendor,
            "os": self.os,
        }


@dataclass(frozen=True, slots=True)
class ArpScanResult:
    """Structured ARP scan outcome used by the CLI and export layers."""

    subnet: str
    timeout: int | None
    devices: tuple[ArpHost, ...]
    os_note: str = HEURISTIC_OS_NOTE

    def to_dict(self) -> dict[str, Any]:
        """Return the stable JSON-serializable representation."""
        return {
            "subnet": self.subnet,
            "timeout": self.timeout,
            "devices": [device.to_dict() for device in self.devices],
            "os_note": self.os_note,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ArpScanResult":
        """Build a typed ARP result from JSON-like data."""
        subnet = _require_string(payload, "subnet")
        raw_devices = payload.get("devices")
        if not isinstance(raw_devices, list):
            raise ParseError("ARP reports must contain a 'devices' array.")

        timeout = _optional_int(payload.get("timeout"), field_name="timeout")
        os_note = _optional_string(payload.get("os_note")) or HEURISTIC_OS_NOTE
        devices = tuple(ArpHost.from_payload(item) for item in raw_devices if isinstance(item, Mapping))

        if len(devices) != len(raw_devices):
            raise ParseError("ARP report devices must be objects with ip and mac fields.")

        return cls(subnet=subnet, timeout=timeout, devices=devices, os_note=os_note)


SupportedExportReport = TracerouteResult | ArpScanResult


def parse_supported_report_payload(payload: Mapping[str, Any]) -> SupportedExportReport:
    """Parse a supported exported report into its typed model."""
    if "hops" in payload and "host" in payload:
        return TracerouteResult.from_payload(payload)
    if "devices" in payload and "subnet" in payload:
        return ArpScanResult.from_payload(payload)

    raise ReportExportError(
        "Unsupported report type. report-export only accepts traceroute or arp-scan JSON exports."
    )


def _require_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ParseError(f"Report field '{key}' must be a non-empty string.")
    return value


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ParseError("Expected a string field in the report payload.")
    return value


def _optional_int(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ParseError(f"Report field '{field_name}' must be an integer.") from exc
