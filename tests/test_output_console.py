from __future__ import annotations

from hir.core.models import ArpScanResult, PingResult, TracerouteHop, TracerouteResult
from hir.output.console import render_arp_console, render_ping_console, render_traceroute_console


def test_render_ping_console_includes_summary_stats() -> None:
    result = PingResult.from_rtt(host="1.1.1.1", count=2, timeout=1, rtt_values=[10.1, 12.3])
    rendered = render_ping_console(result)

    assert "Ping report for 1.1.1.1" in rendered
    assert "Sent: 2  Received: 2" in rendered
    assert "min=10.10" in rendered
    assert "avg=11.20" in rendered
    assert "max=12.30" in rendered


def test_render_ping_console_handles_empty_reply_set() -> None:
    rendered = render_ping_console(
        PingResult.from_rtt(host="1.1.1.1", count=4, timeout=1, rtt_values=[])
    )

    assert "No ICMP replies were parsed from ping output." in rendered


def test_render_traceroute_console_formats_nan_as_na(traceroute_result: TracerouteResult) -> None:
    rendered = render_traceroute_console(
        TracerouteResult(
            host=traceroute_result.host,
            max_hops=traceroute_result.max_hops,
            timeout=traceroute_result.timeout,
            hops=(
                traceroute_result.hops[0],
                TracerouteHop(hop=4, ip="198.51.100.5", rtt_ms=float("nan")),
            ),
        )
    )

    assert "Traceroute report for example.com" in rendered
    assert "192.168.1.1" in rendered
    assert "n/a" in rendered


def test_render_arp_console_displays_headers_and_devices(arp_result: ArpScanResult) -> None:
    rendered = render_arp_console(arp_result)

    assert "ARP scan report for 192.168.1.0/24" in rendered
    assert "Heuristic OS guess" in rendered
    assert "192.168.1.10" in rendered
    assert "Test Vendor" in rendered


def test_render_arp_console_handles_empty_discovery_set() -> None:
    rendered = render_arp_console(
        ArpScanResult(
            subnet="192.168.1.0/24",
            timeout=1,
            devices=(),
        )
    )

    assert "No devices were discovered." in rendered
