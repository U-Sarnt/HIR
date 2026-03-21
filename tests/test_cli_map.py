import hir.cli as cli_mod
import hir.core.network as network_mod


class DummyConsole:
    def __init__(self):
        self.messages = []

    def print(self, *args, **kwargs):
        self.messages.append(" ".join(str(arg) for arg in args))


def test_cmd_map_console_marks_os_as_estimated(monkeypatch):
    answers = iter(["192.168.1.0/24", "1", "c"])
    console = DummyConsole()

    monkeypatch.setattr(cli_mod, "prompt", lambda _message: next(answers))
    monkeypatch.setattr(cli_mod, "console", console)
    monkeypatch.setattr(
        network_mod,
        "enhanced_arp_scan",
        lambda subnet, timeout: [{"ip": "192.168.1.10", "mac": "aa:bb:cc:dd:ee:ff"}],
    )
    monkeypatch.setattr(network_mod, "get_vendor_from_mac", lambda _mac: "Test Vendor")
    monkeypatch.setattr(network_mod, "hybrid_os_fingerprint", lambda _ip: "Linux/Unix")

    cli_mod.cmd_map()

    assert any("SO estimado" in message for message in console.messages)
    assert any("estimación heurística" in message for message in console.messages)
    assert any("Posible Linux/Unix (heurístico)" in message for message in console.messages)


def test_cmd_map_json_reports_insufficient_data_for_unknown_os(monkeypatch):
    answers = iter(["192.168.1.0/24", "1", "j"])
    console = DummyConsole()
    captured = {}

    monkeypatch.setattr(cli_mod, "prompt", lambda _message: next(answers))
    monkeypatch.setattr(cli_mod, "console", console)
    monkeypatch.setattr(
        network_mod,
        "enhanced_arp_scan",
        lambda subnet, timeout: [{"ip": "192.168.1.10", "mac": "aa:bb:cc:dd:ee:ff"}],
    )
    monkeypatch.setattr(network_mod, "get_vendor_from_mac", lambda _mac: "Test Vendor")
    monkeypatch.setattr(network_mod, "hybrid_os_fingerprint", lambda _ip: "Desconocido")

    def fake_dump_json(data, base_filename=None, directory="results/json"):
        captured["data"] = data
        return "/tmp/arp.json"

    monkeypatch.setattr(cli_mod, "dump_json", fake_dump_json)

    cli_mod.cmd_map()

    assert captured["data"]["devices"][0]["os"] == "Sin datos suficientes"
    assert any("JSON >> /tmp/arp.json" in message for message in console.messages)
