"""Shared filesystem helpers for export backends."""

from __future__ import annotations

import os
from pathlib import Path


def build_output_path(
    directory: str | Path,
    *,
    base_filename: str | None,
    suffix: str,
    default_base_filename: str,
) -> Path:
    """Return the next sequential export path for a backend."""
    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)

    existing_count = sum(1 for path in output_dir.iterdir() if path.suffix == suffix)
    index = existing_count + 1
    stem = base_filename or default_base_filename
    separator = "_" if stem else ""
    filename = f"{stem}{separator}{index:02d}{suffix}"
    return output_dir / filename


def finalize_output_path(path: Path) -> None:
    """Apply the permissive file mode expected by the current workflow."""
    try:
        path.chmod(0o644)
        sudo_uid = os.environ.get("SUDO_UID")
        sudo_gid = os.environ.get("SUDO_GID")
        if sudo_uid and sudo_gid:
            os.chown(path, int(sudo_uid), int(sudo_gid))
    except PermissionError:
        pass
