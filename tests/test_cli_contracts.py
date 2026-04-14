from __future__ import annotations

import json
from pathlib import Path

import pytest

import hir.cli as cli_mod
from hir.cli_contracts import ExitCode
from hir.core.errors import PrivilegeRequiredError
from hir.core.models import PingResult


def test_help_writes_only_to_stdout(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli_mod.main(["--help"])

    captured = capsys.readouterr()

    assert exc_info.value.code == ExitCode.SUCCESS
    assert "Usage: hir [OPTIONS] COMMAND [ARGS]..." in captured.out
    assert captured.err == ""


def test_usage_errors_use_stderr_and_stable_exit_code(tmp_path: Path, capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli_mod.main(["ping", "127.0.0.1", "--format", "console", "--output-dir", str(tmp_path)])

    captured = capsys.readouterr()

    assert exc_info.value.code == ExitCode.USAGE_ERROR
    assert captured.out == ""
    assert "--output-dir can only be used with --format json or --format html." in captured.err


def test_runtime_errors_use_stderr_and_stable_exit_code(monkeypatch, capsys) -> None:
    def raise_runtime_error(name: str, **_kwargs: object) -> PingResult:
        assert name == "ping"
        raise PrivilegeRequiredError("root privileges are required")

    monkeypatch.setattr(cli_mod, "_run_provider", raise_runtime_error)

    with pytest.raises(SystemExit) as exc_info:
        cli_mod.main(["ping", "127.0.0.1"])

    captured = capsys.readouterr()

    assert exc_info.value.code == ExitCode.OPERATIONAL_ERROR
    assert captured.out == ""
    assert "root privileges are required" in captured.err


def test_json_export_stdout_contains_only_report_path(monkeypatch, tmp_path: Path, capsys) -> None:
    def fake_run_provider(name: str, **kwargs: object) -> PingResult:
        assert name == "ping"
        return PingResult.from_rtt(
            host=str(kwargs["host"]),
            count=int(kwargs["count"]),
            timeout=int(kwargs["timeout"]),
            rtt_values=[10.1, 12.3],
        )

    monkeypatch.setattr(cli_mod, "_run_provider", fake_run_provider)

    with pytest.raises(SystemExit) as exc_info:
        cli_mod.main(
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
            ]
        )

    captured = capsys.readouterr()

    assert exc_info.value.code == ExitCode.SUCCESS
    assert captured.err == ""

    report_path = Path(captured.out.strip())
    assert report_path.name == "ping_1_1_1_1_01.json"
    assert json.loads(report_path.read_text(encoding="utf-8"))["report_type"] == "ping"
