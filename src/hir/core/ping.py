import subprocess
from typing import List

def ping_host(host: str, count: int = 4, timeout: int = 2) -> List[float]:
    """
    Ejecuta `ping -c <count> -W <timeout> <host>` y devuelve la lista de tiempos (ms).
    Lanza RuntimeError en caso de fallo.
    """
    cmd = [
        "ping",
        "-c", str(count),
        "-W", str(timeout),
        host,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        # Comando falló
        raise RuntimeError(f"ping falló ({host}): {proc.stderr.strip()}")

    times: List[float] = []
    for line in proc.stdout.splitlines():
        if "time=" in line:
            # Extrae el número tras "time=" (hasta el siguiente espacio)
            try:
                part = line.split("time=")[1].split()[0]  # e.g. "12.3"
                times.append(float(part))
            except (IndexError, ValueError):
                continue
    return times

