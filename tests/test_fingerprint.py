from __future__ import annotations

import subprocess
import sys
import types

import hir.core.fingerprint as fingerprint_mod
from hir.core.models import UNKNOWN_OS


class CompletedProcess:
    def __init__(self, stdout: str) -> None:
        self.stdout = stdout


def test_os_fingerprint_nmap_parses_os_details(monkeypatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: CompletedProcess("Host up\nOS details: TestOS 1.0\n"),
    )

    assert fingerprint_mod.os_fingerprint_nmap("127.0.0.1") == "TestOS 1.0"


def test_os_fingerprint_nmap_returns_unknown_when_binary_missing(monkeypatch) -> None:
    def raise_missing_binary(*_args, **_kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", raise_missing_binary)

    assert fingerprint_mod.os_fingerprint_nmap("127.0.0.1") == UNKNOWN_OS


def test_os_fingerprint_ttl_parses_reply_line_from_ping_output(monkeypatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: CompletedProcess(
            "PING host\n64 bytes from 1.1.1.1: icmp_seq=1 ttl=128 time=10.1 ms\n"
        ),
    )

    assert fingerprint_mod.os_fingerprint_ttl("1.1.1.1") == "Windows"


def test_os_fingerprint_ttl_returns_unknown_without_ttl(monkeypatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: CompletedProcess("PING host\n"),
    )

    assert fingerprint_mod.os_fingerprint_ttl("1.1.1.1") == UNKNOWN_OS


def test_os_fingerprint_scapy_uses_window_size_heuristic(monkeypatch) -> None:
    scapy_package = types.ModuleType("scapy")
    scapy_all = types.ModuleType("scapy.all")

    class FakePacket:
        def __init__(self, layers: list[object]) -> None:
            self.layers = layers

        def __truediv__(self, other: object) -> "FakePacket":
            return FakePacket([*self.layers, other])

    class FakeIP:
        def __init__(self, *, dst: str) -> None:
            self.dst = dst

        def __truediv__(self, other: object) -> FakePacket:
            return FakePacket([("ip", self.dst), other])

    class FakeTCP:
        def __init__(self, *, dport: int, flags: str) -> None:
            self.dport = dport
            self.flags = flags

    class FakeResponse:
        def __init__(self, window: int) -> None:
            self.window = window

        def haslayer(self, _layer: object) -> bool:
            return True

        def __getitem__(self, _layer: object) -> object:
            return types.SimpleNamespace(window=self.window)

    responses = iter([FakeResponse(2048)])
    scapy_all.IP = FakeIP
    scapy_all.TCP = FakeTCP
    scapy_all.sr1 = lambda *_args, **_kwargs: next(responses)
    monkeypatch.setitem(sys.modules, "scapy", scapy_package)
    monkeypatch.setitem(sys.modules, "scapy.all", scapy_all)

    assert fingerprint_mod.os_fingerprint_scapy("192.0.2.10") == "Linux/Unix"


def test_os_fingerprint_scapy_falls_back_to_cisco_probe(monkeypatch) -> None:
    scapy_package = types.ModuleType("scapy")
    scapy_all = types.ModuleType("scapy.all")

    class FakePacket:
        def __init__(self, layers: list[object]) -> None:
            self.layers = layers

        def __truediv__(self, other: object) -> "FakePacket":
            return FakePacket([*self.layers, other])

    class FakeIP:
        def __init__(self, *, dst: str) -> None:
            self.dst = dst

        def __truediv__(self, other: object) -> FakePacket:
            return FakePacket([("ip", self.dst), other])

    class FakeTCP:
        def __init__(self, *, dport: int, flags: str) -> None:
            self.dport = dport
            self.flags = flags

    responses = iter([None, object()])
    scapy_all.IP = FakeIP
    scapy_all.TCP = FakeTCP
    scapy_all.sr1 = lambda *_args, **_kwargs: next(responses)
    monkeypatch.setitem(sys.modules, "scapy", scapy_package)
    monkeypatch.setitem(sys.modules, "scapy.all", scapy_all)

    assert fingerprint_mod.os_fingerprint_scapy("192.0.2.10") == "Cisco IOS"


def test_os_fingerprint_scapy_returns_unknown_when_import_fails(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "scapy", types.ModuleType("scapy"))
    monkeypatch.setitem(sys.modules, "scapy.all", types.ModuleType("scapy.all"))

    assert fingerprint_mod.os_fingerprint_scapy("192.0.2.10") == UNKNOWN_OS


def test_os_fingerprint_snmp_parses_sysdescr(monkeypatch) -> None:
    nmap_module = types.ModuleType("nmap")

    class FakePortScanner:
        def scan(self, ip: str, arguments: str) -> None:
            assert ip == "192.0.2.10"
            assert arguments == "-sU -p161 --script=snmp-info"

        def all_hosts(self) -> list[str]:
            return ["192.0.2.10"]

        def __getitem__(self, host: str):
            assert host == "192.0.2.10"
            return {"udp": {161: {"script": {"snmp-info": "SysDescr: RouterOS"}}}}

    nmap_module.PortScanner = FakePortScanner
    monkeypatch.setitem(sys.modules, "nmap", nmap_module)

    assert fingerprint_mod.os_fingerprint_snmp("192.0.2.10") == "RouterOS"


def test_hybrid_os_fingerprint_returns_first_non_unknown_guess(monkeypatch) -> None:
    monkeypatch.setattr(fingerprint_mod, "os_fingerprint_nmap", lambda _ip: UNKNOWN_OS)
    monkeypatch.setattr(fingerprint_mod, "os_fingerprint_scapy", lambda _ip: "Linux/Unix")
    monkeypatch.setattr(
        fingerprint_mod,
        "os_fingerprint_ttl",
        lambda _ip: (_ for _ in ()).throw(RuntimeError("should not run")),
    )

    assert fingerprint_mod.hybrid_os_fingerprint("192.0.2.10") == "Linux/Unix"


def test_hybrid_os_fingerprint_returns_unknown_when_all_detectors_fail(monkeypatch) -> None:
    monkeypatch.setattr(
        fingerprint_mod,
        "os_fingerprint_nmap",
        lambda _ip: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    monkeypatch.setattr(fingerprint_mod, "os_fingerprint_scapy", lambda _ip: UNKNOWN_OS)
    monkeypatch.setattr(fingerprint_mod, "os_fingerprint_ttl", lambda _ip: UNKNOWN_OS)
    monkeypatch.setattr(fingerprint_mod, "os_fingerprint_snmp", lambda _ip: UNKNOWN_OS)

    assert fingerprint_mod.hybrid_os_fingerprint("192.0.2.10") == UNKNOWN_OS
