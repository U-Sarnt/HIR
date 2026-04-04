import json
from pathlib import Path

from hir.output.contracts import REPORT_DOCUMENT_SCHEMA, REPORT_DOCUMENT_SCHEMA_VERSION
from hir.output.json import dump_json


def test_dump_json_writes_expected_content_and_sequence(tmp_path):
    out_path_1 = dump_json(
        {
            "host": "1.1.1.1",
            "count": 2,
            "timeout": 1,
            "rtt_ms": [10.1, 12.3],
            "received": 2,
            "min_ms": 10.1,
            "avg_ms": 11.2,
            "max_ms": 12.3,
        },
        base_filename="scan",
        directory=str(tmp_path),
    )
    out_path_2 = dump_json(
        {
            "host": "1.1.1.2",
            "count": 1,
            "timeout": 1,
            "rtt_ms": [],
            "received": 0,
            "min_ms": None,
            "avg_ms": None,
            "max_ms": None,
        },
        base_filename="scan",
        directory=str(tmp_path),
    )

    assert Path(out_path_1).name == "scan_01.json"
    assert Path(out_path_2).name == "scan_02.json"
    assert json.loads(Path(out_path_1).read_text(encoding="utf-8")) == {
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


def test_dump_json_accepts_versioned_document_and_normalizes_legacy_shapes(tmp_path):
    out_path = dump_json(
        {
            "schema": REPORT_DOCUMENT_SCHEMA,
            "schema_version": REPORT_DOCUMENT_SCHEMA_VERSION,
            "report_type": "traceroute",
            "report": {
                "host": "example.com",
                "hops": [[1, "192.168.1.1", 1.23]],
            },
        },
        directory=str(tmp_path),
    )

    assert Path(out_path).name == "01.json"
    assert json.loads(Path(out_path).read_text(encoding="utf-8")) == {
        "schema": REPORT_DOCUMENT_SCHEMA,
        "schema_version": REPORT_DOCUMENT_SCHEMA_VERSION,
        "report_type": "traceroute",
        "report": {
            "host": "example.com",
            "max_hops": None,
            "timeout": None,
            "hops": [{"hop": 1, "ip": "192.168.1.1", "rtt_ms": 1.23}],
        },
    }
