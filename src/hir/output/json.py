"""JSON report export and loading helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from hir.core.errors import ParseError, ReportExportError
from hir.core.models import (
    ArpScanResult,
    PingResult,
    SupportedExportReport,
    TracerouteResult,
    parse_supported_report_payload,
)
from hir.output.files import build_output_path, finalize_output_path

SerializableReport = Mapping[str, Any] | PingResult | TracerouteResult | ArpScanResult


def dump_json(
    data: SerializableReport,
    base_filename: str | None = None,
    directory: str | Path = "results/json",
) -> str:
    """Serialize a report payload to a sequential JSON file."""
    payload = _coerce_json_payload(data)
    out_path = build_output_path(
        directory,
        base_filename=base_filename,
        suffix=".json",
        default_base_filename="",
    )

    with out_path.open("w", encoding="utf-8") as output_file:
        json.dump(payload, output_file, indent=2, ensure_ascii=False)

    finalize_output_path(out_path)
    return str(out_path)


def load_report(report_path: str | Path) -> SupportedExportReport:
    """Load a supported exported JSON report into its typed model."""
    path = Path(report_path)

    try:
        raw_data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ReportExportError(f"Unable to read report file: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ParseError(f"Report file is not valid JSON: {path}") from exc

    if not isinstance(raw_data, dict):
        raise ParseError("Report file must contain a top-level JSON object.")

    return parse_supported_report_payload(raw_data)


def _coerce_json_payload(data: SerializableReport) -> dict[str, Any]:
    if isinstance(data, Mapping):
        return dict(data)
    return data.to_dict()
