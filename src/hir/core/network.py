"""Compatibility facade over the split network-related modules.

New code should import directly from `hir.core.arp`, `hir.core.fingerprint`,
and `hir.core.vendor`.
"""

from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor

from hir.core.arp import enhanced_arp_scan, run_arp_scan, scan_arp_hosts
from hir.core.fingerprint import (
    hybrid_os_fingerprint,
    os_fingerprint_nmap,
    os_fingerprint_scapy,
    os_fingerprint_snmp,
    os_fingerprint_ttl,
)
from hir.core.vendor import OUI_DATABASE_UNAVAILABLE, get_vendor_from_mac, load_oui_database

__all__ = [
    "OUI_DATABASE_UNAVAILABLE",
    "enhanced_arp_scan",
    "get_vendor_from_mac",
    "hybrid_os_fingerprint",
    "load_oui_database",
    "os_fingerprint_nmap",
    "os_fingerprint_scapy",
    "os_fingerprint_snmp",
    "os_fingerprint_ttl",
    "port_scan",
    "run_arp_scan",
    "scan_arp_hosts",
]


def port_scan(ip: str, ports: list[int], timeout: float = 1.0) -> dict[int, bool]:
    """Run a lightweight TCP connect scan against the provided ports."""

    def _scan_port(port: int) -> tuple[int, bool]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((ip, port))
            return port, True
        except OSError:
            return port, False
        finally:
            sock.close()

    with ThreadPoolExecutor(max_workers=50) as executor:
        return dict(executor.map(_scan_port, ports))
