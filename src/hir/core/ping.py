import subprocess
from collections.abc import Iterable, Iterator
from typing import List, NamedTuple


class PingReply(NamedTuple):
    ttl: int | None
    time_ms: float | None
    time_text: str | None


def _validate_ping_params(host: str, count: int | None = 4, timeout: int = 2) -> None:
    if not host.strip():
        raise ValueError("El host no puede estar vacío.")
    if count is not None and count < 1:
        raise ValueError("La cantidad de paquetes debe ser mayor o igual que 1.")
    if timeout < 1:
        raise ValueError("El timeout debe ser mayor o igual que 1.")


def build_ping_command(host: str, count: int | None = 4, timeout: int = 2) -> list[str]:
    """Construye el comando ping validando los parámetros básicos."""
    _validate_ping_params(host, count, timeout)

    cmd = ["ping"]
    if count is not None:
        cmd.extend(["-c", str(count)])
    cmd.extend(["-W", str(timeout), host])
    return cmd


def parse_ping_line(line: str) -> PingReply | None:
    """Parsea una línea de respuesta ICMP y devuelve sus campos relevantes."""
    if "bytes from" not in line or "time=" not in line:
        return None

    ttl = None
    time_ms = None
    time_text = None

    for part in line.split():
        if part.startswith("ttl="):
            try:
                ttl = int(part.split("=", 1)[1])
            except ValueError:
                ttl = None
        elif part.startswith("time="):
            time_text = part.split("=", 1)[1]
            try:
                time_ms = float(time_text)
            except ValueError:
                time_ms = None

    return PingReply(ttl=ttl, time_ms=time_ms, time_text=time_text)


def iter_ping_replies(lines: Iterable[str]) -> Iterator[PingReply]:
    """Itera solo por líneas de respuesta ICMP ya parseadas."""
    for line in lines:
        reply = parse_ping_line(line)
        if reply is not None:
            yield reply


def ping_host(host: str, count: int = 4, timeout: int = 2) -> List[float]:
    """
    Ejecuta `ping -c <count> -W <timeout> <host>` y devuelve la lista de tiempos (ms).
    Lanza RuntimeError en caso de fallo.
    """
    cmd = build_ping_command(host, count=count, timeout=timeout)

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "El comando 'ping' no está instalado o no está disponible en PATH."
        ) from exc

    if proc.returncode != 0:
        error = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"ping falló ({host}): {error}")

    return [
        reply.time_ms
        for reply in iter_ping_replies(proc.stdout.splitlines())
        if reply.time_ms is not None
    ]
