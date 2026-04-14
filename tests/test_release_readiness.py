from __future__ import annotations

import subprocess
import sys
from importlib.metadata import version

from hir import __version__


def test_distribution_metadata_matches_package_version() -> None:
    assert version("hir") == __version__


def test_python_module_entry_point_exposes_cli_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "hir", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == f"hir, version {__version__}"
    assert result.stderr == ""
