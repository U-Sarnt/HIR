"""Console renderers for the validated HIR commands."""

from __future__ import annotations

import math

from hir.core.models import ArpScanResult, PingResult, TracerouteResult


def render_ping_console(result: PingResult) -> str:
    """Return the validated console output for ping results."""
    lines = [
        f"Ping report for {result.host}",
        f"Sent: {result.count}  Received: {result.received}",
    ]

    if result.received:
        lines.append(
            "RTT ms: "
            f"min={result.min_ms:.2f} "
            f"avg={result.avg_ms:.2f} "
            f"max={result.max_ms:.2f}"
        )
    else:
        lines.append("No ICMP replies were parsed from ping output.")

    return "\n".join(lines)


def render_traceroute_console(result: TracerouteResult) -> str:
    """Return the validated console output for traceroute results."""
    lines = [f"Traceroute report for {result.host}"]
    if not result.hops:
        lines.append("No hops were parsed from traceroute output.")
        return "\n".join(lines)

    for hop in result.hops:
        lines.append(f"{hop.hop:>2}  {hop.ip:<15}  {_format_rtt(hop.rtt_ms)}")

    return "\n".join(lines)


def render_arp_console(result: ArpScanResult) -> str:
    """Return the validated console output for ARP scan results."""
    lines = [
        f"ARP scan report for {result.subnet}",
        "OS results are heuristic guesses based on available network signals.",
    ]

    if not result.devices:
        lines.append("No devices were discovered.")
        return "\n".join(lines)

    lines.append(f"{'IP':<15} {'MAC':<17} {'Vendor':<20} Heuristic OS guess")
    for device in result.devices:
        lines.append(
            f"{device.ip:<15} {device.mac:<17} "
            f"{device.vendor:<20} {device.os}"
        )

    return "\n".join(lines)


def _format_rtt(value: float) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.2f} ms"
