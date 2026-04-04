from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from hir.core.models import ArpScanResult, TracerouteResult

_FIXTURES_DIR = Path(__file__).parent / "fixtures" / "reports"


def _load_report_payload(filename: str) -> dict[str, Any]:
    return json.loads((_FIXTURES_DIR / filename).read_text(encoding="utf-8"))


@pytest.fixture
def traceroute_payload() -> dict[str, Any]:
    return _load_report_payload("traceroute_report.json")


@pytest.fixture
def arp_payload() -> dict[str, Any]:
    return _load_report_payload("arp_report.json")


@pytest.fixture
def traceroute_result(traceroute_payload: dict[str, Any]) -> TracerouteResult:
    return TracerouteResult.from_payload(traceroute_payload)


@pytest.fixture
def arp_result(arp_payload: dict[str, Any]) -> ArpScanResult:
    return ArpScanResult.from_payload(arp_payload)
