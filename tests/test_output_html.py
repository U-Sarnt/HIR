from pathlib import Path

import pytest
from jinja2 import TemplateNotFound

import hir.output.html as html_mod
from hir.output.html import render_html


def test_render_html_arp_report_has_complete_content(tmp_path):
    out_path = render_html(
        {
            "subnet": "192.168.1.0/24",
            "devices": [
                {
                    "ip": "192.168.1.10",
                    "mac": "aa:bb:cc:dd:ee:ff",
                    "vendor": "Test Vendor",
                    "os": "Posible Linux/Unix (heurístico)",
                }
            ],
        },
        base_filename="arp_report",
        directory=str(tmp_path),
    )

    html = Path(out_path).read_text(encoding="utf-8")

    assert "<title>Reporte ARP - 192.168.1.0/24</title>" in html
    assert "Generado:" in html
    assert "Sistema operativo estimado" in html
    assert "estimación heurística" in html
    assert "192.168.1.10" in html
    assert "Test Vendor" in html
    assert "Posible Linux/Unix (heurístico)" in html
    assert "resto de tu HTML" not in html
    assert "{{" not in html
    assert "{%" not in html


def test_render_html_arp_report_shows_empty_message(tmp_path):
    out_path = render_html(
        {"subnet": "192.168.1.0/24", "devices": []},
        base_filename="arp_report_empty",
        directory=str(tmp_path),
    )

    html = Path(out_path).read_text(encoding="utf-8")

    assert "No se encontraron dispositivos para la subred indicada." in html


def test_render_html_arp_report_defaults_missing_os_to_insufficient_data(tmp_path):
    out_path = render_html(
        {
            "subnet": "192.168.1.0/24",
            "devices": [
                {
                    "ip": "192.168.1.20",
                    "mac": "aa:bb:cc:dd:ee:00",
                    "vendor": "Test Vendor",
                }
            ],
        },
        base_filename="arp_report_no_os",
        directory=str(tmp_path),
    )

    html = Path(out_path).read_text(encoding="utf-8")

    assert "Sin datos suficientes" in html


def test_render_html_traceroute_template_does_not_depend_on_cwd(tmp_path, monkeypatch):
    external_cwd = tmp_path / "external-cwd"
    external_cwd.mkdir()
    monkeypatch.chdir(external_cwd)

    out_path = render_html(
        {"host": "example.com", "hops": [(1, "192.168.1.1", 1.23)]},
        base_filename="traceroute_report",
        directory=str(tmp_path / "out"),
    )

    html = Path(out_path).read_text(encoding="utf-8")

    assert "<title>Reporte Traceroute" in html
    assert "example.com" in html
    assert "192.168.1.1" in html


def test_render_html_missing_template_fails_honestly(tmp_path, monkeypatch):
    monkeypatch.setattr(
        html_mod,
        "_select_template_name",
        lambda _data: "missing_template.html.j2",
    )

    with pytest.raises(TemplateNotFound, match="missing_template.html.j2"):
        render_html(
            {"subnet": "192.168.1.0/24", "devices": []},
            base_filename="arp_report_missing",
            directory=str(tmp_path),
        )
