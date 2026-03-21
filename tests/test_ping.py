import pytest
from hir.core.ping import ping_host

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

