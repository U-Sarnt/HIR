"""Vendor lookup helpers for MAC address enrichment."""

from __future__ import annotations

import csv
from collections.abc import Iterator
from importlib.resources import files
from pathlib import Path
from typing import IO

from hir.core.models import UNKNOWN_VENDOR

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


def lookup_vendor_from_oui(mac: str) -> str:
    """Return the vendor label from the builtin OUI database only."""
    if not load_oui_database():
        return OUI_DATABASE_UNAVAILABLE

    prefix = mac.replace(":", "").replace("-", "").lower()[:6]
    return _OUI_DB.get(prefix, UNKNOWN_VENDOR)


def get_vendor_from_mac(mac: str) -> str:
    """Resolve a vendor label through the registered vendor-resolver chain."""
    from hir.plugins.runtime import get_runtime_registry

    saw_resolver = False
    saw_unknown = False
    saw_unavailable = False
    for resolver in get_runtime_registry().iter_vendor_resolvers():
        saw_resolver = True
        try:
            vendor = resolver.resolver(mac)
        except Exception:
            continue

        if not vendor:
            continue
        if vendor == UNKNOWN_VENDOR:
            saw_unknown = True
            continue
        if vendor == OUI_DATABASE_UNAVAILABLE:
            saw_unavailable = True
            continue
        return vendor

    if saw_unknown:
        return UNKNOWN_VENDOR
    if saw_unavailable or not saw_resolver:
        return OUI_DATABASE_UNAVAILABLE
    return UNKNOWN_VENDOR


def _iter_oui_rows(path: str | None) -> Iterator[tuple[str, str]]:
    if path is not None:
        with Path(path).open(newline="", encoding="utf-8") as csv_file:
            yield from _read_oui_rows(csv_file)
        return

    resource = files("hir.core").joinpath("oui.csv")
    with resource.open("r", encoding="utf-8") as csv_file:
        yield from _read_oui_rows(csv_file)


def _read_oui_rows(csv_file: IO[str]) -> Iterator[tuple[str, str]]:
    reader = csv.reader(csv_file)
    for row in reader:
        if len(row) < 2:
            continue

        prefix = row[0].strip()
        vendor = row[1].strip()
        if prefix and vendor:
            yield prefix, vendor
