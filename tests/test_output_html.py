from pathlib import Path

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
                    "os": "Linux/Unix",
                }
            ],
        },
        base_filename="arp_report",
        directory=str(tmp_path),
    )

    html = Path(out_path).read_text(encoding="utf-8")

    assert "<title>Reporte ARP - 192.168.1.0/24</title>" in html
    assert "Generado:" in html
    assert "192.168.1.10" in html
    assert "Test Vendor" in html
    assert "Linux/Unix" in html
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
