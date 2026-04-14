import subprocess

import hir.core.vendor as vendor_mod
from hir.core.fingerprint import os_fingerprint_nmap
from hir.core.vendor import OUI_DATABASE_UNAVAILABLE, get_vendor_from_mac, load_oui_database


class Dummy:
    stdout = "OS details: TestOS 1.0"
def fake_run(*args, **kwargs):
    return Dummy()

def test_nmap(monkeypatch):
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert os_fingerprint_nmap("127.0.0.1") == "TestOS 1.0"


def reset_oui_cache():
    vendor_mod._OUI_DB = {}
    vendor_mod._OUI_DB_AVAILABLE = None


def test_vendor_lookup_reports_missing_oui_database():
    reset_oui_cache()

    assert load_oui_database() is False
    assert get_vendor_from_mac("AA:BB:CC:11:22:33") == OUI_DATABASE_UNAVAILABLE


def test_vendor_lookup_uses_mocked_oui_database(tmp_path):
    reset_oui_cache()
    oui_file = tmp_path / "oui.csv"
    oui_file.write_text("aabbcc,Test Vendor\n", encoding="utf-8")

    assert load_oui_database(str(oui_file)) is True
    assert get_vendor_from_mac("AA:BB:CC:11:22:33") == "Test Vendor"
    assert get_vendor_from_mac("DD:EE:FF:11:22:33") == "Desconocido"
