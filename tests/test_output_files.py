from __future__ import annotations

import stat
from pathlib import Path

from hir.output.files import build_output_path, finalize_output_path, normalize_output_base_filename


def test_build_output_path_creates_directory_and_counts_matching_suffixes(tmp_path: Path) -> None:
    (tmp_path / "scan_01.json").write_text("{}", encoding="utf-8")
    (tmp_path / "scan_02.html").write_text("<html></html>", encoding="utf-8")

    out_path = build_output_path(
        tmp_path / "nested",
        base_filename="scan",
        suffix=".json",
        default_base_filename="",
    )

    assert out_path.parent.exists()
    assert out_path.name == "scan_01.json"

    next_path = build_output_path(
        tmp_path,
        base_filename="scan",
        suffix=".json",
        default_base_filename="",
    )
    assert next_path.name == "scan_02.json"


def test_build_output_path_ignores_other_stems_when_incrementing(tmp_path: Path) -> None:
    (tmp_path / "scan_01.json").write_text("{}", encoding="utf-8")
    (tmp_path / "other_99.json").write_text("{}", encoding="utf-8")

    out_path = build_output_path(
        tmp_path,
        base_filename="scan",
        suffix=".json",
        default_base_filename="",
    )

    assert out_path.name == "scan_02.json"


def test_finalize_output_path_sets_mode_and_sudo_owner(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "report.html"
    path.write_text("<html></html>", encoding="utf-8")

    seen: list[tuple[Path, int, int]] = []

    monkeypatch.setenv("SUDO_UID", "1000")
    monkeypatch.setenv("SUDO_GID", "1001")
    monkeypatch.setattr(
        "hir.output.files.os.chown",
        lambda target, uid, gid: seen.append((Path(target), uid, gid)),
    )

    finalize_output_path(path)

    assert stat.S_IMODE(path.stat().st_mode) == 0o644
    assert seen == [(path, 1000, 1001)]


def test_finalize_output_path_ignores_permission_errors(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "report.html"
    path.write_text("<html></html>", encoding="utf-8")

    def raise_permission_error(_self: Path, _mode: int) -> None:
        raise PermissionError("nope")

    monkeypatch.setattr(Path, "chmod", raise_permission_error)

    finalize_output_path(path)


def test_normalize_output_base_filename_strips_managed_sequence() -> None:
    assert normalize_output_base_filename("traceroute_example_com_01") == "traceroute_example_com"
    assert normalize_output_base_filename("traceroute_example_com") == "traceroute_example_com"
