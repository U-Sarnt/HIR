from __future__ import annotations

import errno

import pytest

import hir.core.arp as arp_mod
from hir.core.errors import HIRError, PrivilegeRequiredError
from hir.core.models import ArpHost


class FakePacket:
    def __init__(self, layers: list[tuple[str, str]]) -> None:
        self.layers = layers

    def __truediv__(self, other: tuple[str, str]) -> "FakePacket":
        return FakePacket([*self.layers, other])


class FakeResponse:
    def __init__(self, psrc: str, hwsrc: str) -> None:
        self.psrc = psrc
        self.hwsrc = hwsrc


def _install_fake_scapy(monkeypatch, srp_impl) -> None:
    monkeypatch.setattr(arp_mod, "Ether", lambda *, dst: FakePacket([("ether", dst)]))
    monkeypatch.setattr(arp_mod, "ARP", lambda *, pdst: ("arp", pdst))
    monkeypatch.setattr(arp_mod, "srp", srp_impl)


def test_scan_arp_hosts_builds_broadcast_packet_and_parses_responses(monkeypatch) -> None:
    seen: dict[str, object] = {}

    def fake_srp(packet: FakePacket, timeout: int, verbose: int):
        seen["layers"] = packet.layers
        seen["timeout"] = timeout
        seen["verbose"] = verbose
        return (
            [
                (object(), FakeResponse("192.168.1.10", "aa:bb:cc:dd:ee:ff")),
                (object(), FakeResponse("192.168.1.20", "aa:bb:cc:dd:ee:00")),
            ],
            object(),
        )

    _install_fake_scapy(monkeypatch, fake_srp)

    hosts = arp_mod.scan_arp_hosts("192.168.1.0/24", timeout=2)

    assert seen == {
        "layers": [("ether", "ff:ff:ff:ff:ff:ff"), ("arp", "192.168.1.0/24")],
        "timeout": 2,
        "verbose": 0,
    }
    assert hosts == [
        ArpHost(ip="192.168.1.10", mac="aa:bb:cc:dd:ee:ff"),
        ArpHost(ip="192.168.1.20", mac="aa:bb:cc:dd:ee:00"),
    ]


def test_scan_arp_hosts_converts_privilege_errors_to_actionable_message(monkeypatch) -> None:
    def raise_permission_error(*_args, **_kwargs):
        raise OSError(errno.EPERM, "Operation not permitted")

    _install_fake_scapy(monkeypatch, raise_permission_error)

    with pytest.raises(PrivilegeRequiredError, match="raw-socket capabilities"):
        arp_mod.scan_arp_hosts("192.168.1.0/24")


def test_scan_arp_hosts_wraps_other_runtime_errors(monkeypatch) -> None:
    def raise_runtime_error(*_args, **_kwargs):
        raise RuntimeError("boom")

    _install_fake_scapy(monkeypatch, raise_runtime_error)

    with pytest.raises(HIRError, match="ARP scan failed: boom"):
        arp_mod.scan_arp_hosts("192.168.1.0/24")


def test_scan_arp_hosts_rejects_windows_runtime(monkeypatch) -> None:
    monkeypatch.setattr(arp_mod.platform, "system", lambda: "Windows")

    with pytest.raises(HIRError, match="not supported on Windows"):
        arp_mod.scan_arp_hosts("192.168.1.0/24")


def test_run_arp_scan_enriches_results_and_tolerates_fingerprint_failures(monkeypatch) -> None:
    monkeypatch.setattr(
        arp_mod,
        "scan_arp_hosts",
        lambda _subnet, timeout: [
            ArpHost(ip="192.168.1.10", mac="aa:bb:cc:dd:ee:ff"),
            ArpHost(ip="192.168.1.20", mac="aa:bb:cc:dd:ee:00"),
        ],
    )
    monkeypatch.setattr(
        arp_mod,
        "get_vendor_from_mac",
        lambda mac: {
            "aa:bb:cc:dd:ee:ff": "Test Vendor",
            "aa:bb:cc:dd:ee:00": "Desconocido",
        }[mac],
    )

    def fake_fingerprint(ip: str) -> str:
        if ip.endswith(".20"):
            raise RuntimeError("transient failure")
        return "Linux/Unix"

    monkeypatch.setattr(arp_mod, "hybrid_os_fingerprint", fake_fingerprint)

    result = arp_mod.run_arp_scan("192.168.1.0/24", timeout=3)

    assert result.subnet == "192.168.1.0/24"
    assert result.timeout == 3
    assert result.devices == (
        ArpHost(
            ip="192.168.1.10",
            mac="aa:bb:cc:dd:ee:ff",
            vendor="Test Vendor",
            os="Posible Linux/Unix (heurístico)",
        ),
        ArpHost(
            ip="192.168.1.20",
            mac="aa:bb:cc:dd:ee:00",
            vendor="Desconocido",
            os="Sin datos suficientes",
        ),
    )


def test_enhanced_arp_scan_preserves_legacy_ip_mac_shape(monkeypatch) -> None:
    monkeypatch.setattr(
        arp_mod,
        "scan_arp_hosts",
        lambda _subnet, timeout: [ArpHost(ip="192.168.1.10", mac="aa:bb:cc:dd:ee:ff")],
    )

    assert arp_mod.enhanced_arp_scan("192.168.1.0/24", timeout=2) == [
        {"ip": "192.168.1.10", "mac": "aa:bb:cc:dd:ee:ff"}
    ]


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (PermissionError("denied"), True),
        (OSError(errno.EACCES, "denied"), True),
        (RuntimeError("Cannot set filter"), True),
        (RuntimeError("different failure"), False),
    ],
)
def test_is_privilege_error_matches_expected_signals(exc: BaseException, expected: bool) -> None:
    assert arp_mod._is_privilege_error(exc) is expected
