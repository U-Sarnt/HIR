import sys, time, os, subprocess
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from prompt_toolkit import prompt
from hir.core.network import enhanced_arp_scan, get_vendor_from_mac, hybrid_os_fingerprint
from hir.core.ping import build_ping_command, parse_ping_line
from hir.core.traceroute import traceroute_host
from hir.output.json import dump_json
from hir.output.html import render_html


try:
    from hir_ext import fast_ping, fast_traceroute
except ImportError:
    fast_ping = None
    fast_traceroute = None

console = Console()


def _format_os_guess(raw_os: str | None) -> str:
    if not raw_os or raw_os == "Desconocido":
        return "Sin datos suficientes"
    return f"Posible {raw_os} (heurístico)"

def _prompt_int(
    message: str,
    default: int | None = None,
    empty_value: int | None = None,
    empty_hint: str | None = None,
    minimum: int | None = None,
) -> int | None:
    """Lee enteros de forma segura y evita tracebacks por entradas triviales inválidas."""
    while True:
        raw = prompt(message).strip()
        if raw == "":
            return default if default is not None else empty_value

        try:
            value = int(raw)
        except ValueError:
            hint = ""
            if default is not None:
                hint = " Pulsa Enter para usar el valor por defecto."
            elif empty_hint:
                hint = f" Pulsa Enter para {empty_hint}."
            console.print(f"[red]Entrada no válida '{raw}'. Introduce un número entero.{hint}[/]")
            continue

        if minimum is not None and value < minimum:
            console.print(
                f"[red]Entrada no válida '{raw}'. Introduce un número entero mayor o igual que {minimum}.[/]"
            )
            continue

        return value


def _prompt_required_text(message: str, field_name: str) -> str | None:
    value = prompt(message).strip()
    if value:
        return value

    console.print(f"[red]{field_name} no puede estar vacío.[/]")
    console.print()
    return None


def _prompt_output_format() -> str:
    fmt_input = prompt("Formato (console[c]/json[j]/html[h]) » ").strip().lower()
    fmt = {
        "c": "console",
        "console": "console",
        "j": "json",
        "json": "json",
        "h": "html",
        "html": "html",
    }.get(fmt_input)
    if fmt is None:
        console.print(f"[red]Formato no válido '{fmt_input}', usando 'console' por defecto[/]")
        return "console"
    return fmt

def splash():
    console.clear()
    console.print(Panel.fit("[bold cyan]HIR – Herramienta para Ingenieros de Redes[/]"), justify="center")
    with console.status("[green]Cargando módulos…[/]", spinner="dots"):
        time.sleep(0.5)
    console.print()

def menu_loop():
    while True:
        console.print("[bold]Menú de opciones principales:[/]")
        console.print("  [green]1)[/] Ping      [green]2)[/] Traceroute      [green]clear[/] (Limpia)")
        console.print("  [green]3)[/] ARP_Oscan [green]0)[/] Salir")
        opt = prompt("Selecciona opción » ").strip().lower()

        if opt in ("0", "q"):
            console.print("👋 ¡Hasta luego!")
            sys.exit(0)

        if opt == "clear":
            # Usar clear de sistema para limpiar todo el buffer visible
            os.system("clear")
            continue

        if opt == "1":
            cmd_ping()
        elif opt == "2":
            cmd_traceroute()
        elif opt == "3":
            cmd_map()
        else:
            console.print("[red]Opción no válida[/]\n")

def cmd_ping():
    """Ejecuta ping en tiempo real, soporta Ctrl+C y modo continuo."""
    host = _prompt_required_text("Host/IP » ", "Host/IP")
    if host is None:
        return

    count = _prompt_int(
        "Paquetes (4) / Enter para continuo sin fin » ",
        empty_value=None,
        empty_hint="activar el modo continuo",
        minimum=1,
    )
    timeout = _prompt_int("Timeout (2s) » ", default=2, minimum=1)

    try:
        cmd = build_ping_command(host, count=count, timeout=timeout)
    except ValueError as e:
        console.print(f"[red]ERROR:[/] {e}")
        console.print()
        return

    modo = "continuo" if count is None else f"{count} paquetes"    
    print(" ")
    console.print(f":satellite: Ping a [bold]{host}[/] - {modo}, timeout: {timeout}s", style="cyan")
    console.print("TTL    Tipo    Tiempo")

    # Ejecuta ping y captura interrupción
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    error_lines = []
    try:
        for raw in proc.stdout or ():
            reply = parse_ping_line(raw)
            if reply is None:
                line = raw.strip()
                if line:
                    error_lines.append(line)
                continue

            ttl = "-" if reply.ttl is None else str(reply.ttl)
            tiempo = reply.time_text or "-"
            console.print(f"[magenta]{ttl:<6}[/] [yellow]ICMP  [/]  {tiempo} ms")
    except KeyboardInterrupt:
        # Interrupción del usuario
        console.print("\n[bold red]Ping interrumpido por usuario. Volviendo al menú...[/]")
        proc.terminate()
        proc.wait()
        console.print()
        return

    returncode = proc.wait()
    if returncode != 0:
        detail = f": {error_lines[-1]}" if error_lines else ""
        console.print(f"[red]ERROR:[/] ping falló ({host}){detail}")
    console.print()

def cmd_traceroute():
    host = _prompt_required_text("Host/IP » ", "Host/IP")
    if host is None:
        return

    max_hops = _prompt_int("Hops (30) » ", default=30, minimum=1)
    timeout = _prompt_int("Timeout (2s) » ", default=2, minimum=1)
    fmt = _prompt_output_format()

    fn = fast_traceroute or traceroute_host
    try:
        hops = fn(host, max_hops, timeout)
    except Exception as e:
        console.print(f"[red]ERROR:[/] {e}")
        console.print()
        return

    data = {"host": host, "hops": hops}

    if fmt == "console":
        print(" ")
        console.print(f"[bold]Traceroute a {host}:[/]")
        for hop, ip, rtt in hops:            
            console.print(f"[{hop:02d}] {ip} — {rtt} ms")
    elif fmt == "json":
        out = dump_json(data, base_filename=f"{host}_tr")
        console.print(f"[green]JSON >> {out}[/]")
    else:
        out = render_html(data, base_filename=f"{host}_tr")
        console.print(f"[green]HTML >> {out}[/]")

    console.print()

def cmd_map():
    """Realiza ARP scan y muestra una estimación heurística de SO."""
    host_subnet = _prompt_required_text("Rango/Subred (ej. 192.168.1.0/24) » ", "Rango/Subred")
    if host_subnet is None:
        return

    timeout = _prompt_int("Timeout ARP (1s) » ", default=1, minimum=1)
    fmt = _prompt_output_format()

    print(" ")
    console.print(f":globe_with_meridians: Mapeando subred {host_subnet} (timeout {timeout}s)...", style="cyan")
    
    # Importar las funciones correctas
    from hir.core.network import enhanced_arp_scan, get_vendor_from_mac, hybrid_os_fingerprint
    
    try:
        # Usar el nombre correcto de la función
        devices = enhanced_arp_scan(host_subnet, timeout)
    except Exception as e:
        console.print(f"[red]Error ARP scan:[/] {e}")
        return

    # Estimación heurística de SO para cada host
    for dev in devices:
        # Vendor lookup
        dev['vendor'] = get_vendor_from_mac(dev['mac'])
        try:
            dev['os'] = _format_os_guess(hybrid_os_fingerprint(dev['ip']))
        except Exception:
            dev['os'] = _format_os_guess(None)
    
    data = {"subnet": host_subnet, "devices": devices}

    # Output según formato
    if fmt == "console":
        print(" ")
        console.print(f"[bold]Dispositivos encontrados en {host_subnet}:[/]")
        console.print("[dim]El sistema operativo mostrado es una estimación heurística basada en las señales disponibles.[/]")
        print(" ")
        console.print("IP               MAC                Vendor         SO estimado")
        for d in devices:
            console.print(f"{d['ip']:<16} {d['mac']:<18} {d['vendor']:<13} {d['os']}")
    elif fmt == "json":
        out = dump_json(data, base_filename=f"arpmap_{host_subnet.replace('/','_')}")
        console.print(f"[green]JSON >> {out}[/]")
    else:
        out = render_html(data, base_filename=f"arpmap_{host_subnet.replace('/','_')}")
        console.print(f"[green]HTML >> {out}[/]")
    console.print()

def main():
    splash()
    menu_loop()

if __name__ == "__main__":
    main()
