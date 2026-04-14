"""Shared filesystem helpers for export backends."""

from __future__ import annotations

import os
import re
from pathlib import Path

_OUTPUT_INDEX_PATTERN = re.compile(r"^(?P<stem>.*?)(?:_(?P<index>\d{2}))?$")


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

    stem = base_filename or default_base_filename
    index = _next_output_index(output_dir, stem=stem, suffix=suffix)
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


def normalize_output_base_filename(base_filename: str) -> str:
    """Strip the managed numeric suffix used by sequential exports."""
    match = _OUTPUT_INDEX_PATTERN.fullmatch(base_filename)
    if match is None:
        return base_filename

    stem = match.group("stem")
    index = match.group("index")
    if stem and index:
        return stem
    return base_filename


def _next_output_index(output_dir: Path, *, stem: str, suffix: str) -> int:
    seen_indexes: list[int] = []

    for path in output_dir.iterdir():
        if path.suffix != suffix:
            continue

        index = _extract_index(path=path, stem=stem)
        if index is not None:
            seen_indexes.append(index)

    return max(seen_indexes, default=0) + 1


def _extract_index(path: Path, *, stem: str) -> int | None:
    separator = "_" if stem else ""
    prefix = f"{stem}{separator}"

    if not path.stem.startswith(prefix):
        return None

    index_text = path.stem[len(prefix) :]
    if len(index_text) != 2 or not index_text.isdigit():
        return None

    return int(index_text)
