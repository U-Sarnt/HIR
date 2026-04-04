"""Best-effort host fingerprinting helpers."""

from __future__ import annotations

import re
import subprocess

from hir.core.models import UNKNOWN_OS


def os_fingerprint_nmap(ip: str) -> str:
    """Try to estimate the OS using `nmap -O --osscan-guess`."""
    try:
        result = subprocess.run(
            ["nmap", "-O", "--osscan-guess", "-Pn", ip],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return UNKNOWN_OS

    match = re.search(r"OS details:\s*(.+)", result.stdout)
    return match.group(1) if match else UNKNOWN_OS


def os_fingerprint_scapy(ip: str, timeout: float = 1.0) -> str:
    """Send lightweight TCP probes through Scapy for a heuristic OS guess."""
    try:
        from scapy.all import IP, TCP, sr1
    except Exception:
        return UNKNOWN_OS

    try:
        syn = IP(dst=ip) / TCP(dport=80, flags="S")
        response = sr1(syn, timeout=timeout, verbose=0)
        if response and response.haslayer(TCP):
            window = response[TCP].window
            return "Linux/Unix" if window % 1024 == 0 else "Windows"

        xmas = IP(dst=ip) / TCP(dport=80, flags="FPU")
        response = sr1(xmas, timeout=timeout, verbose=0)
    except Exception:
        return UNKNOWN_OS

    return "Cisco IOS" if response else UNKNOWN_OS


def os_fingerprint_ttl(ip: str) -> str:
    """Infer an OS family from the TTL of a single ping reply."""
    try:
        proc = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return UNKNOWN_OS

    match = re.search(r"ttl=(\d+)", proc.stdout, re.IGNORECASE)
    if not match:
        return UNKNOWN_OS

    ttl = int(match.group(1))
    if ttl >= 128:
        return "Windows"
    if ttl >= 64:
        return "Linux/Unix"
    return UNKNOWN_OS


def os_fingerprint_snmp(ip: str) -> str:
    """Try to recover an OS clue from SNMP sysDescr data when available."""
    try:
        import nmap

        scanner = nmap.PortScanner()
        scanner.scan(ip, arguments="-sU -p161 --script=snmp-info")
        for host in scanner.all_hosts():
            info = scanner[host]["udp"][161]["script"]["snmp-info"]
            match = re.search(r"SysDescr:\s*(.+)", info)
            return match.group(1) if match else UNKNOWN_OS
    except Exception:
        return UNKNOWN_OS

    return UNKNOWN_OS


def hybrid_os_fingerprint(ip: str) -> str:
    """Return the first non-empty heuristic OS guess available."""
    for detector in (
        os_fingerprint_nmap,
        os_fingerprint_scapy,
        os_fingerprint_ttl,
        os_fingerprint_snmp,
    ):
        try:
            result = detector(ip)
        except Exception:
            continue

        if result != UNKNOWN_OS:
            return result

    return UNKNOWN_OS
