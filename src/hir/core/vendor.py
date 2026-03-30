"""Vendor lookup helpers for MAC address enrichment."""

from __future__ import annotations

import csv
from collections.abc import Iterator
from importlib.resources import files
from pathlib import Path

OUI_DATABASE_UNAVAILABLE = "Base OUI no disponible"

_OUI_DB: dict[str, str] = {}
_OUI_DB_AVAILABLE: bool | None = None


def load_oui_database(path: str | None = None) -> bool:
    """Load the packaged or provided OUI database into the in-memory cache."""
    global _OUI_DB, _OUI_DB_AVAILABLE

    if path is None and _OUI_DB_AVAILABLE is not None:
        return _OUI_DB_AVAILABLE

    _OUI_DB = {}

    try:
        for prefix, vendor in _iter_oui_rows(path):
            _OUI_DB[prefix.lower()] = vendor
    except OSError:
        _OUI_DB_AVAILABLE = False
        return False

    _OUI_DB_AVAILABLE = True
    return True


def get_vendor_from_mac(mac: str) -> str:
    """Return the vendor label for the first three MAC bytes."""
    if not load_oui_database():
        return OUI_DATABASE_UNAVAILABLE

    prefix = mac.replace(":", "").replace("-", "").lower()[:6]
    return _OUI_DB.get(prefix, "Desconocido")


def _iter_oui_rows(path: str | None) -> Iterator[tuple[str, str]]:
    if path is not None:
        with Path(path).open(newline="", encoding="utf-8") as csv_file:
            yield from _read_oui_rows(csv_file)
        return

    resource = files("hir.core").joinpath("oui.csv")
    with resource.open("r", newline="", encoding="utf-8") as csv_file:
        yield from _read_oui_rows(csv_file)


def _read_oui_rows(csv_file) -> Iterator[tuple[str, str]]:
    reader = csv.reader(csv_file)
    for row in reader:
        if len(row) < 2:
            continue

        prefix = row[0].strip()
        vendor = row[1].strip()
        if prefix and vendor:
            yield prefix, vendor
