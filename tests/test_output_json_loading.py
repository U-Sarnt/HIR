from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from hir.core.errors import ParseError, ReportExportError
from hir.core.models import ArpScanResult, TracerouteResult
from hir.output.contracts import REPORT_DOCUMENT_SCHEMA, REPORT_DOCUMENT_SCHEMA_VERSION
from hir.output.json import dump_json, load_report


def test_load_report_parses_traceroute_fixture(
    tmp_path: Path,
    traceroute_payload: dict[str, Any],
) -> None:
    report_path = tmp_path / "traceroute.json"
    report_path.write_text(json.dumps(traceroute_payload), encoding="utf-8")

    report = load_report(report_path)

    assert isinstance(report, TracerouteResult)
    assert report.host == "example.com"
    assert len(report.hops) == 3


def test_load_report_parses_arp_fixture(tmp_path: Path, arp_payload: dict[str, Any]) -> None:
    report_path = tmp_path / "arp.json"
    report_path.write_text(json.dumps(arp_payload), encoding="utf-8")

    report = load_report(report_path)

    assert isinstance(report, ArpScanResult)
    assert report.subnet == "192.168.1.0/24"
    assert len(report.devices) == 2


def test_load_report_parses_versioned_document(
    tmp_path: Path,
    traceroute_payload: dict[str, Any],
) -> None:
    report_path = tmp_path / "traceroute.json"
    report_path.write_text(
        json.dumps(
            {
                "schema": REPORT_DOCUMENT_SCHEMA,
                "schema_version": REPORT_DOCUMENT_SCHEMA_VERSION,
                "report_type": "traceroute",
                "report": traceroute_payload,
            }
        ),
        encoding="utf-8",
    )

    report = load_report(report_path)

    assert isinstance(report, TracerouteResult)
    assert report.host == "example.com"
    assert len(report.hops) == 3


def test_load_report_rejects_non_object_json(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

    with pytest.raises(ParseError, match="top-level JSON object"):
        load_report(report_path)


def test_load_report_rejects_invalid_json(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text("{invalid", encoding="utf-8")

    with pytest.raises(ParseError, match="not valid JSON"):
        load_report(report_path)


def test_load_report_raises_export_error_for_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ReportExportError, match="Unable to read report file"):
        load_report(tmp_path / "missing.json")


def test_load_report_rejects_unsupported_schema_version(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "schema": REPORT_DOCUMENT_SCHEMA,
                "schema_version": 99,
                "report_type": "traceroute",
                "report": {"host": "example.com", "hops": []},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ParseError, match="Unsupported report schema version"):
        load_report(report_path)


def test_dump_json_accepts_typed_report_models(
    tmp_path: Path,
    traceroute_result: TracerouteResult,
) -> None:
    out_path = dump_json(traceroute_result, base_filename="trace", directory=tmp_path)

    assert Path(out_path).name == "trace_01.json"
    assert json.loads(Path(out_path).read_text(encoding="utf-8"))["report"]["host"] == "example.com"


def test_dump_json_rejects_unknown_mapping_shape(tmp_path: Path) -> None:
    with pytest.raises(ReportExportError, match="Unsupported report type"):
        dump_json({"status": "ok"}, directory=tmp_path)
