from hir.core.traceroute import traceroute_host


class FakeCompletedProcess:
    def __init__(self, stdout, returncode=0, stderr=""):
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = stderr


def test_traceroute_parses_hostname_and_ip(monkeypatch):
    output = (
        "traceroute to example.com (93.184.216.34), 30 hops max\n"
        " 1  router.local (192.168.1.1)  1.23 ms\n"
    )
    monkeypatch.setattr(
        "hir.core.traceroute.subprocess.run",
        lambda *args, **kwargs: FakeCompletedProcess(output),
    )

    hops = traceroute_host("example.com")

    assert hops == [(1, "192.168.1.1", 1.23)]


def test_traceroute_parses_ip_only(monkeypatch):
    output = (
        "traceroute to 1.1.1.1 (1.1.1.1), 30 hops max\n"
        " 1  10.0.0.1  4.56 ms\n"
    )
    monkeypatch.setattr(
        "hir.core.traceroute.subprocess.run",
        lambda *args, **kwargs: FakeCompletedProcess(output),
    )

    hops = traceroute_host("1.1.1.1")

    assert hops == [(1, "10.0.0.1", 4.56)]
