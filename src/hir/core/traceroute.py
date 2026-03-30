"""Traceroute collection and parsing helpers."""

from __future__ import annotations

import re
import subprocess

from hir.core.errors import CommandExecutionError, DependencyMissingError
from hir.core.models import TracerouteHop, TracerouteResult


def build_traceroute_command(host: str, max_hops: int = 30, timeout: int = 2) -> list[str]:
    """Build the system traceroute command after basic validation."""
    _validate_traceroute_params(host, max_hops, timeout)
    return ["traceroute", "-m", str(max_hops), "-w", str(timeout), host]


def parse_traceroute_line(line: str) -> TracerouteHop | None:
    """Parse one traceroute output line into a hop model."""
    parts = line.split()
    if not parts:
        return None

    try:
        hop = int(parts[0])
    except ValueError:
        return None

    match = re.search(r"\(([^)]+)\)", line)
    if match:
        ip = match.group(1)
    else:
        if len(parts) < 2 or parts[1] == "*":
            return None
        ip = parts[1].strip("()")

    rtt_match = re.search(r"(\d+\.\d+)\s*ms", line)
    rtt_ms = float(rtt_match.group(1)) if rtt_match else float("nan")
    return TracerouteHop(hop=hop, ip=ip, rtt_ms=rtt_ms)


def traceroute_host(host: str, max_hops: int = 30, timeout: int = 2) -> list[tuple[int, str, float]]:
    """Return the parsed traceroute hops as legacy tuples."""
    return [hop.to_tuple() for hop in run_traceroute(host, max_hops=max_hops, timeout=timeout).hops]


def run_traceroute(host: str, max_hops: int = 30, timeout: int = 2) -> TracerouteResult:
    """Run `traceroute` and return a structured result model."""
    cmd = build_traceroute_command(host, max_hops=max_hops, timeout=timeout)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise DependencyMissingError(
            "El comando 'traceroute' no está instalado. Instálalo (p. ej. `sudo apt install traceroute`) y vuelve a intentarlo."
        ) from exc

    if proc.returncode not in (0, 1):
        error = proc.stderr.strip() or proc.stdout.strip()
        raise CommandExecutionError(f"traceroute falló ({host}): {error}")

    hops = tuple(
        hop
        for line in proc.stdout.splitlines()[1:]
        if (hop := parse_traceroute_line(line)) is not None
    )
    return TracerouteResult(host=host, max_hops=max_hops, timeout=timeout, hops=hops)


def _validate_traceroute_params(host: str, max_hops: int, timeout: int) -> None:
    if not host.strip():
        raise ValueError("El host no puede estar vacío.")
    if max_hops < 1:
        raise ValueError("La cantidad máxima de saltos debe ser mayor o igual que 1.")
    if timeout < 1:
        raise ValueError("El timeout debe ser mayor o igual que 1.")
