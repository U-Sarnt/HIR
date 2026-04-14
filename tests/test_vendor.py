from __future__ import annotations

from io import StringIO

import pytest

import hir.core.vendor as vendor_mod


@pytest.fixture(autouse=True)
def reset_vendor_cache() -> None:
    vendor_mod._OUI_DB = {}
    vendor_mod._OUI_DB_AVAILABLE = None


def test_load_oui_database_caches_packaged_result(monkeypatch) -> None:
    calls = {"count": 0}

    def fake_iter_rows(path):
        calls["count"] += 1
        yield ("aabbcc", "Test Vendor")

    monkeypatch.setattr(vendor_mod, "_iter_oui_rows", fake_iter_rows)

    assert vendor_mod.load_oui_database() is True
    assert vendor_mod.load_oui_database() is True
    assert calls["count"] == 1


def test_get_vendor_from_mac_normalizes_mac_formats(tmp_path) -> None:
    oui_file = tmp_path / "oui.csv"
    oui_file.write_text("aabbcc,Test Vendor\n", encoding="utf-8")

    assert vendor_mod.load_oui_database(str(oui_file)) is True
    assert vendor_mod.get_vendor_from_mac("AA:BB:CC:11:22:33") == "Test Vendor"
    assert vendor_mod.get_vendor_from_mac("AA-BB-CC-11-22-33") == "Test Vendor"


def test_read_oui_rows_skips_incomplete_entries() -> None:
    rows = list(
        vendor_mod._read_oui_rows(
            StringIO("aabbcc,Vendor One\ninvalid\n,Missing Prefix\n112233,Vendor Two\n")
        )
    )

    assert rows == [("aabbcc", "Vendor One"), ("112233", "Vendor Two")]
