from __future__ import annotations

import math
from typing import Any

import pytest

from hir.core.errors import ParseError, ReportExportError
from hir.core.models import (
    INSUFFICIENT_OS_DATA,
    ArpHost,
    ArpScanResult,
    PingResult,
    TracerouteHop,
    TracerouteResult,
    format_os_guess,
    parse_supported_report_payload,
)


def test_ping_result_from_rtt_computes_derived_metrics() -> None:
    result = PingResult.from_rtt(
        host="1.1.1.1",
        count=3,
        timeout=1,
        rtt_values=[10.0, 12.0, 8.0],
    )

    assert result.received == 3
    assert result.min_ms == 8.0
    assert result.avg_ms == pytest.approx(10.0)
    assert result.max_ms == 12.0
    assert result.to_dict()["rtt_ms"] == [10.0, 12.0, 8.0]


def test_ping_result_from_rtt_handles_missing_replies() -> None:
    result = PingResult.from_rtt(host="1.1.1.1", count=4, timeout=1, rtt_values=[])

    assert result.received == 0
    assert result.min_ms is None
    assert result.avg_ms is None
    assert result.max_ms is None


def test_ping_result_from_payload_recomputes_derived_fields() -> None:
    result = PingResult.from_payload(
        {
            "host": "1.1.1.1",
            "count": 3,
            "timeout": 1,
            "rtt_ms": [10.0, 12.0, 8.0],
            "received": 3,
        }
    )

    assert result.received == 3
    assert result.min_ms == 8.0
    assert result.avg_ms == pytest.approx(10.0)
    assert result.max_ms == 12.0


def test_ping_result_from_payload_rejects_mismatched_received() -> None:
    with pytest.raises(ParseError, match="must match the number of RTT values"):
        PingResult.from_payload(
            {
                "host": "1.1.1.1",
                "count": 2,
                "timeout": 1,
                "rtt_ms": [10.0],
                "received": 2,
            }
        )


def test_traceroute_result_round_trips_fixture(
    traceroute_payload: dict[str, Any],
    traceroute_result: TracerouteResult,
) -> None:
    assert traceroute_result.to_dict() == {
        **traceroute_payload,
        "hops": [
            {"hop": 1, "ip": "192.168.1.1", "rtt_ms": 1.23},
            {"hop": 2, "ip": "203.0.113.10", "rtt_ms": 12.5},
            {"hop": 3, "ip": "93.184.216.34", "rtt_ms": 23.45},
        ],
    }


def test_traceroute_hop_from_payload_defaults_missing_rtt_to_nan() -> None:
    hop = TracerouteHop.from_payload([3, "203.0.113.10"])

    assert hop.hop == 3
    assert hop.ip == "203.0.113.10"
    assert math.isnan(hop.rtt_ms)


def test_traceroute_hop_from_payload_accepts_mapping() -> None:
    hop = TracerouteHop.from_payload({"hop": 3, "ip": "203.0.113.10", "rtt_ms": 7.5})

    assert hop == TracerouteHop(hop=3, ip="203.0.113.10", rtt_ms=7.5)


@pytest.mark.parametrize("payload", [[], ["hop-only"], ["one", "1.1.1.1", "slow"]])
def test_traceroute_hop_from_payload_rejects_invalid_shapes(payload: list[Any]) -> None:
    with pytest.raises(ParseError):
        TracerouteHop.from_payload(payload)


def test_arp_host_from_discovery_keeps_os_wording_honest() -> None:
    assert format_os_guess(None) == INSUFFICIENT_OS_DATA
    assert ArpHost.from_discovery(
        ip="192.168.1.10",
        mac="aa:bb:cc:dd:ee:ff",
        vendor="Test Vendor",
        raw_os="Linux/Unix",
    ) == ArpHost(
        ip="192.168.1.10",
        mac="aa:bb:cc:dd:ee:ff",
        vendor="Test Vendor",
        os="Posible Linux/Unix (heurístico)",
    )


def test_arp_scan_result_rejects_non_mapping_devices() -> None:
    with pytest.raises(ParseError, match="devices must be objects"):
        ArpScanResult.from_payload(
            {
                "subnet": "192.168.1.0/24",
                "devices": [{"ip": "192.168.1.10", "mac": "aa:bb:cc:dd:ee:ff"}, "bad"],
            }
        )


def test_parse_supported_report_payload_dispatches_known_reports(
    arp_payload: dict[str, Any],
    traceroute_payload: dict[str, Any],
) -> None:
    assert isinstance(parse_supported_report_payload(traceroute_payload), TracerouteResult)
    assert isinstance(parse_supported_report_payload(arp_payload), ArpScanResult)


def test_parse_supported_report_payload_rejects_unknown_shape() -> None:
    with pytest.raises(ReportExportError, match="Unsupported report type"):
        parse_supported_report_payload({"host": "example.com"})
