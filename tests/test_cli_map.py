import json
from pathlib import Path

from click.testing import CliRunner

import hir.cli as cli_mod


def test_arp_scan_permission_failure_is_actionable(monkeypatch):
    def raise_permission_error(_subnet: str, timeout: int):
        raise PermissionError("Operation not permitted")

    monkeypatch.setattr(cli_mod, "enhanced_arp_scan", raise_permission_error)

    result = CliRunner().invoke(cli_mod.cli, ["arp-scan", "192.168.1.0/24"])

    assert result.exit_code != 0
    assert "root privileges" in result.output
    assert "CAP_NET_RAW" in result.output
    assert "Traceback" not in result.output


def test_arp_scan_console_keeps_os_wording_honest(monkeypatch):
    monkeypatch.setattr(
        cli_mod,
        "enhanced_arp_scan",
        lambda _subnet, timeout: [{"ip": "192.168.1.10", "mac": "aa:bb:cc:dd:ee:ff"}],
    )
    monkeypatch.setattr(cli_mod, "get_vendor_from_mac", lambda _mac: "Test Vendor")
    monkeypatch.setattr(cli_mod, "hybrid_os_fingerprint", lambda _ip: "Linux/Unix")

    result = CliRunner().invoke(cli_mod.cli, ["arp-scan", "192.168.1.0/24"])

    assert result.exit_code == 0
    assert "OS results are heuristic guesses" in result.output
    assert "Heuristic OS guess" in result.output
    assert "Posible Linux/Unix (heurístico)" in result.output
    assert "accuracy" not in result.output.lower()


def test_report_export_renders_supported_json_report(tmp_path):
    report_path = tmp_path / "traceroute.json"
    report_path.write_text(
        json.dumps({"host": "example.com", "hops": [[1, "192.168.1.1", 1.23]]}),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli_mod.cli,
        ["report-export", str(report_path), "--output-dir", str(tmp_path / "html")],
    )

    assert result.exit_code == 0

    html_path = Path(result.output.strip())
    html = html_path.read_text(encoding="utf-8")

    assert html_path.name == "traceroute_01.html"
    assert "<title>Reporte Traceroute" in html
    assert "example.com" in html
    assert "192.168.1.1" in html
