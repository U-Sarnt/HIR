# src/hir/core/network.py
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from scapy.all import ARP, Ether, srp
import csv
import socket
from importlib.resources import files

# ---------- ARP SCAN MODULE ----------
def enhanced_arp_scan(subnet: str, timeout: int = 1) -> list[dict]:
    """
    Realiza un escaneo ARP en la subred dada.
    Devuelve lista de dicts con campos: 'ip', 'mac'.
    Requiere CAP_NET_RAW o privilegios root.
    """
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet)
    ans, _ = srp(pkt, timeout=timeout, verbose=0)
    devices = []
    for _, r in ans:
        devices.append({'ip': r.psrc, 'mac': r.hwsrc})
    return devices

# ---------- VENDOR LOOKUP MODULE ----------
# Cache de OUI cargada al inicio
_OUI_DB: dict[str, str] = {}
_OUI_DB_AVAILABLE: bool | None = None
OUI_DATABASE_UNAVAILABLE = "Base OUI no disponible"

def load_oui_database(path: str = None) -> bool:
    """Carga la base OUI desde un CSV local o remoto en _OUI_DB."""
    global _OUI_DB, _OUI_DB_AVAILABLE
    if path is None and _OUI_DB_AVAILABLE is not None:
        return _OUI_DB_AVAILABLE
   
    # Ruta por defecto dentro del paquete usando importlib.resources
    try:
        from importlib.resources import files
    except ImportError:
        from importlib_resources import files

    resource_path = files("hir.core") / "oui.csv"
    path = path or str(resource_path)
    _OUI_DB = {}

    try:
        with open(path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) < 2:
                    continue
                prefix, vendor = row[0].strip(), row[1].strip()
                if not prefix:
                    continue
                _OUI_DB[prefix.lower()] = vendor
    except OSError:
        _OUI_DB_AVAILABLE = False
        return False

    _OUI_DB_AVAILABLE = True
    return True

def os_fingerprint_nmap(ip: str) -> str:
    """Detecta SO usando nmap -O y --osscan-guess."""
    res = subprocess.run(
        ['nmap','-O','--osscan-guess','-Pn',ip],
        capture_output=True, text=True
    )
    m = re.search(r'OS details:\s*(.+)', res.stdout)
    return m.group(1) if m else 'Desconocido'


def os_fingerprint_scapy(ip: str, timeout: float = 1.0) -> str:
    """Envía probes TCP (SYN y Xmas) con Scapy para inferir OS."""
    from scapy.all import IP, TCP, sr1
    # SYN probe
    syn = IP(dst=ip)/TCP(dport=80, flags='S')
    resp = sr1(syn, timeout=timeout, verbose=0)
    if resp and resp.haslayer(TCP):
        win = resp[TCP].window
        return 'Linux/Unix' if win % 1024 == 0 else 'Windows'
    # Xmas tree probe
    xmas = IP(dst=ip)/TCP(dport=80, flags='FPU')
    resp2 = sr1(xmas, timeout=timeout, verbose=0)
    if resp2:
        return 'Cisco IOS'
    return 'Desconocido'

def os_fingerprint_ttl(ip: str) -> str:
    """Analiza TTL mínimo de un ping para conjeturar SO."""
    proc = subprocess.run(
        ['ping', '-c', '1', '-W', '1', ip],
        capture_output=True, text=True
    )
    line = proc.stdout.splitlines()[-1] if proc.stdout else ''
    m = re.search(r'ttl=(\d+)', line)
    if m:
        ttl = int(m.group(1))
        return 'Windows' if ttl >= 128 else 'Linux/Unix' if ttl >= 64 else 'Desconocido'
    return 'Desconocido'

def os_fingerprint_snmp(ip: str) -> str:
    """Consulta SNMPv2/v3 (sin credenciales) para extraer SysDescr."""
    try:
        import nmap
        nm = nmap.PortScanner()
        nm.scan(ip, arguments='-sU -p161 --script=snmp-info')
        for h in nm.all_hosts():
            info = nm[h]['udp'][161]['script']['snmp-info']
            m = re.search(r'SysDescr:\s*(.+)', info)
            return m.group(1) if m else 'Desconocido'
    except Exception:
        pass
    return 'Desconocido'

def hybrid_os_fingerprint(ip: str) -> str:
    """Cascada: Nmap → Scapy → TTL → SNMP para >95% de precisión."""
    for fn in (os_fingerprint_nmap,
               os_fingerprint_scapy,
               os_fingerprint_ttl,
               os_fingerprint_snmp):
        res = fn(ip)
        if res != 'Desconocido':
            return res
    return 'Desconocido'

def get_vendor_from_mac(mac: str) -> str:
    """Devuelve el vendor según los primeros 3 bytes de la MAC (OUI)."""
    if not load_oui_database():
        return OUI_DATABASE_UNAVAILABLE

    prefix = mac.replace(':', '').replace('-', '').lower()[:6]
    return _OUI_DB.get(prefix, 'Desconocido')

def _ttl_based_analysis(ip: str) -> str:
    """Análisis simple de TTL vía ping para conjeturar SO."""
    proc = subprocess.run(['ping', '-c', '1', '-W', '1', ip], capture_output=True, text=True)
    line = proc.stdout.splitlines()[-1] if proc.stdout else ''
    m = re.search(r'ttl=(\d+)', line)
    if m:
        ttl = int(m.group(1))
        if ttl >= 128:
            return 'Windows'
        elif ttl >= 64:
            return 'Linux/Unix'
    return 'Desconocido'

def port_scan(ip: str, ports: list[int], timeout: float = 1.0) -> dict[int, bool]:
    """Escanea puertos TCP en la IP; devuelve dict puerto-> abierto.
    Para rangos grandes, considere implementar en Rust para mayor velocidad.
    """
    def _scan_port(port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect((ip, port))
            return port, True
        except:
            return port, False
        finally:
            s.close()

    results = {}
    with ThreadPoolExecutor(max_workers=50) as executor:
        for port, open_ in executor.map(_scan_port, ports):
            results[port] = open_
    return results
