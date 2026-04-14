from __future__ import annotations

import socket

import hir.core.arp as arp_mod
import hir.core.fingerprint as fingerprint_mod
import hir.core.network as network_mod
import hir.core.vendor as vendor_mod


def test_network_facade_reexports_phase3_helpers() -> None:
    assert network_mod.run_arp_scan is arp_mod.run_arp_scan
    assert network_mod.scan_arp_hosts is arp_mod.scan_arp_hosts
    assert network_mod.enhanced_arp_scan is arp_mod.enhanced_arp_scan
    assert network_mod.hybrid_os_fingerprint is fingerprint_mod.hybrid_os_fingerprint
    assert network_mod.get_vendor_from_mac is vendor_mod.get_vendor_from_mac
    assert network_mod.OUI_DATABASE_UNAVAILABLE == vendor_mod.OUI_DATABASE_UNAVAILABLE


def test_port_scan_reports_open_and_closed_ports(monkeypatch) -> None:
    created: list["FakeSocket"] = []

    class FakeSocket:
        def __init__(self, *_args: object) -> None:
            self.timeout: float | None = None
            self.closed = False
            created.append(self)

        def settimeout(self, timeout: float) -> None:
            self.timeout = timeout

        def connect(self, address: tuple[str, int]) -> None:
            if address[1] != 22:
                raise OSError("closed")

        def close(self) -> None:
            self.closed = True

    monkeypatch.setattr(
        network_mod.socket,
        "socket",
        lambda *_args: FakeSocket(socket.AF_INET, socket.SOCK_STREAM),
    )

    result = network_mod.port_scan("192.0.2.10", [22, 443], timeout=2.5)

    assert result == {22: True, 443: False}
    assert [sock.timeout for sock in created] == [2.5, 2.5]
    assert all(sock.closed for sock in created)
