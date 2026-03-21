import pytest
from hir.core.ping import build_ping_command, parse_ping_line, ping_host

class FakeProc:
    def __init__(self, returncode, stdout, stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

def sample_output():
    return (
        "PING 1.1.1.1 (1.1.1.1): 56 data bytes\n"
        "64 bytes from 1.1.1.1: icmp_seq=0 ttl=58 time=10.1 ms\n"
        "64 bytes from 1.1.1.1: icmp_seq=1 ttl=58 time=12.3 ms\n"
        "--- 1.1.1.1 ping statistics ---\n"
        "2 packets transmitted, 2 packets received, 0.0% packet loss\n"
    )

def test_ping_success(monkeypatch):
    # Sustituimos subprocess.run para no depender de ping real
    monkeypatch.setattr("subprocess.run", lambda *args, **kw: FakeProc(0, sample_output()))
    times = ping_host("1.1.1.1", count=2, timeout=1)
    assert times == [10.1, 12.3]

def test_ping_failure(monkeypatch):
    # Simulamos fallo del comando
    monkeypatch.setattr("subprocess.run", lambda *args, **kw: FakeProc(1, "", "host unreachable"))
    with pytest.raises(RuntimeError) as exc:
        ping_host("bad.host", count=1, timeout=1)
    assert "host unreachable" in str(exc.value)

def test_build_ping_command_allows_continuous_mode():
    assert build_ping_command("1.1.1.1", count=None, timeout=2) == ["ping", "-W", "2", "1.1.1.1"]

def test_build_ping_command_rejects_invalid_timeout():
    with pytest.raises(ValueError):
        build_ping_command("1.1.1.1", count=1, timeout=0)

def test_parse_ping_line_returns_structured_reply():
    reply = parse_ping_line("64 bytes from 1.1.1.1: icmp_seq=1 ttl=58 time=10.1 ms")
    assert reply is not None
    assert reply.ttl == 58
    assert reply.time_ms == 10.1
    assert reply.time_text == "10.1"
