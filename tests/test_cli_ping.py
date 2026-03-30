import json
from pathlib import Path

import pytest
from click.testing import CliRunner

import hir.cli as cli_mod
from hir.core.models import PingResult, TracerouteHop, TracerouteResult


def test_main_help_entry_path(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli_mod.main(["--help"])

    captured = capsys.readouterr()

    assert exc_info.value.code == 0
    assert "Usage: hir [OPTIONS] COMMAND [ARGS]..." in captured.out
    assert "arp-scan" in captured.out
    assert "report-export" in captured.out


@pytest.mark.parametrize(
    ("args", "expected_text"),
    [
        (["ping", "--help"], "Run ICMP ping against HOST."),
        (["traceroute", "--help"], "Run traceroute against HOST."),
        (["arp-scan", "--help"], "Run an ARP scan against SUBNET."),
        (["report-export", "--help"], "Render a supported JSON report to HTML."),
    ],
)
def test_subcommand_help(args, expected_text):
    result = CliRunner().invoke(cli_mod.cli, args)

    assert result.exit_code == 0
    assert expected_text in result.output


def test_ping_command_wires_backend_and_exports_json(monkeypatch, tmp_path):
    seen: dict[str, object] = {}

    def fake_run_ping(host: str, count: int, timeout: int) -> PingResult:
        seen["args"] = (host, count, timeout)
        return PingResult.from_rtt(host=host, count=count, timeout=timeout, rtt_values=[10.1, 12.3])

    monkeypatch.setattr(cli_mod, "run_ping", fake_run_ping)

    result = CliRunner().invoke(
        cli_mod.cli,
        [
            "ping",
            "1.1.1.1",
            "--count",
            "2",
            "--timeout",
            "1",
            "--format",
            "json",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert seen["args"] == ("1.1.1.1", 2, 1)

    report_path = Path(result.output.strip())
    assert report_path.name == "ping_1_1_1_1_01.json"
    assert json.loads(report_path.read_text(encoding="utf-8")) == {
        "host": "1.1.1.1",
        "count": 2,
        "timeout": 1,
        "rtt_ms": [10.1, 12.3],
        "received": 2,
        "min_ms": 10.1,
        "avg_ms": 11.2,
        "max_ms": 12.3,
    }


def test_traceroute_command_wires_backend(monkeypatch):
    seen: dict[str, object] = {}

    def fake_run_traceroute(host: str, max_hops: int, timeout: int) -> TracerouteResult:
        seen["args"] = (host, max_hops, timeout)
        return TracerouteResult(
            host=host,
            max_hops=max_hops,
            timeout=timeout,
            hops=(TracerouteHop(1, "192.168.1.1", 1.23),),
        )

    monkeypatch.setattr(cli_mod, "run_traceroute", fake_run_traceroute)

    result = CliRunner().invoke(
        cli_mod.cli,
        ["traceroute", "example.com", "--max-hops", "5", "--timeout", "1"],
    )

    assert result.exit_code == 0
    assert seen["args"] == ("example.com", 5, 1)
    assert "Traceroute report for example.com" in result.output
    assert "192.168.1.1" in result.output
