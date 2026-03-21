import subprocess
import re
from typing import List, Tuple

def traceroute_host(host: str, max_hops: int = 30, timeout: int = 2) -> List[Tuple[int, str, float]]:
    cmd = ["traceroute", "-m", str(max_hops), "-w", str(timeout), host]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        raise RuntimeError("El comando 'traceroute' no está instalado. Instálalo (p. ej. `sudo apt install traceroute`) y vuelve a intentarlo.")

    if proc.returncode not in (0, 1):
        raise RuntimeError(f"traceroute falló ({host}): {proc.stderr.strip()}")

    results: List[Tuple[int, str, float]] = []
    for line in proc.stdout.splitlines()[1:]:
        parts = line.split()
        try:
            hop = int(parts[0])
            match = re.search(r"\(([^)]+)\)", line)
            ip = match.group(1) if match else parts[1].strip("()")
            m = re.search(r"(\d+\.\d+)\s*ms", line)
            rtt = float(m.group(1)) if m else float("nan")
            results.append((hop, ip, rtt))
        except (ValueError, IndexError):
            continue

    return results
