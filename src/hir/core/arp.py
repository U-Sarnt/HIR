"""ARP discovery orchestration for the validated HIR workflow."""

from __future__ import annotations

from scapy.all import ARP, Ether, srp

from hir.core.errors import HIRError, PrivilegeRequiredError
from hir.core.fingerprint import hybrid_os_fingerprint
from hir.core.models import ArpHost, ArpScanResult
from hir.core.vendor import get_vendor_from_mac

_PRIVILEGE_ERROR_HINTS = (
    "operation not permitted",
    "permission denied",
    "not permitted",
    "cannot set filter",
)


def run_arp_scan(subnet: str, timeout: int = 1) -> ArpScanResult:
    """Run the validated ARP workflow with best-effort enrichment."""
    devices = []
    for host in scan_arp_hosts(subnet, timeout=timeout):
        vendor = get_vendor_from_mac(host.mac)
        try:
            raw_os = hybrid_os_fingerprint(host.ip)
        except Exception:
            raw_os = None

        devices.append(
            ArpHost.from_discovery(
                ip=host.ip,
                mac=host.mac,
                vendor=vendor,
                raw_os=raw_os,
            )
        )

    return ArpScanResult(subnet=subnet, timeout=timeout, devices=tuple(devices))


def scan_arp_hosts(subnet: str, timeout: int = 1) -> list[ArpHost]:
    """Discover hosts on a subnet using a broadcast ARP request."""
    _validate_arp_params(subnet, timeout)

    packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet)

    try:
        answered, _ = srp(packet, timeout=timeout, verbose=0)
    except Exception as exc:
        if _is_privilege_error(exc):
            raise PrivilegeRequiredError(
                "ARP scan requires root privileges or raw-socket capabilities "
                "(CAP_NET_RAW/CAP_NET_ADMIN). Re-run with sudo or grant the "
                "required capabilities to the Python environment."
            ) from exc
        raise HIRError(f"ARP scan failed: {exc}") from exc

    return [ArpHost(ip=response.psrc, mac=response.hwsrc) for _, response in answered]


def enhanced_arp_scan(subnet: str, timeout: int = 1) -> list[dict[str, str]]:
    """Compatibility wrapper returning only the discovered IP/MAC pairs."""
    return [{"ip": host.ip, "mac": host.mac} for host in scan_arp_hosts(subnet, timeout=timeout)]


def _validate_arp_params(subnet: str, timeout: int) -> None:
    if not subnet.strip():
        raise ValueError("La subred no puede estar vacía.")
    if timeout < 1:
        raise ValueError("El timeout debe ser mayor o igual que 1.")


def _is_privilege_error(exc: BaseException) -> bool:
    if isinstance(exc, PermissionError):
        return True

    if isinstance(exc, OSError) and exc.errno in {1, 13}:
        return True

    message = str(exc).lower()
    return any(hint in message for hint in _PRIVILEGE_ERROR_HINTS)
