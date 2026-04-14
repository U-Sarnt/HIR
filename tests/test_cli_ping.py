import json
from pathlib import Path

import pytest
from click.testing import CliRunner

import hir.cli as cli_mod
from hir.core.models import PingResult, TracerouteHop, TracerouteResult
from hir.output.contracts import REPORT_DOCUMENT_SCHEMA, REPORT_DOCUMENT_SCHEMA_VERSION


def test_main_help_entry_path(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli_mod.main(["--help"])

    captured = capsys.readouterr()

    assert exc_info.value.code == 0
    assert "Usage: hir [OPTIONS] COMMAND [ARGS]..." in captured.out
    assert "arp-scan" in captured.out
    assert "report-export" in captured.out
    assert captured.err == ""


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

    def fake_run_provider(name: str, **kwargs: object) -> PingResult:
        assert name == "ping"
        seen["args"] = (kwargs["host"], kwargs["count"], kwargs["timeout"])
        return PingResult.from_rtt(
            host=str(kwargs["host"]),
            count=int(kwargs["count"]),
            timeout=int(kwargs["timeout"]),
            rtt_values=[10.1, 12.3],
        )

    monkeypatch.setattr(cli_mod, "_run_provider", fake_run_provider)

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
        "schema": REPORT_DOCUMENT_SCHEMA,
        "schema_version": REPORT_DOCUMENT_SCHEMA_VERSION,
        "report_type": "ping",
        "report": {
            "host": "1.1.1.1",
            "count": 2,
            "timeout": 1,
            "rtt_ms": [10.1, 12.3],
            "received": 2,
            "min_ms": 10.1,
            "avg_ms": 11.2,
            "max_ms": 12.3,
        },
    }


def test_traceroute_command_wires_backend(monkeypatch):
    seen: dict[str, object] = {}

    def fake_run_provider(name: str, **kwargs: object) -> TracerouteResult:
        assert name == "traceroute"
        seen["args"] = (kwargs["host"], kwargs["max_hops"], kwargs["timeout"])
        return TracerouteResult(
            host=str(kwargs["host"]),
            max_hops=int(kwargs["max_hops"]),
            timeout=int(kwargs["timeout"]),
            hops=(TracerouteHop(1, "192.168.1.1", 1.23),),
        )

    monkeypatch.setattr(cli_mod, "_run_provider", fake_run_provider)

    result = CliRunner().invoke(
        cli_mod.cli,
        ["traceroute", "example.com", "--max-hops", "5", "--timeout", "1"],
    )

    assert result.exit_code == 0
    assert seen["args"] == ("example.com", 5, 1)
    assert "Traceroute report for example.com" in result.output
    assert "192.168.1.1" in result.output
