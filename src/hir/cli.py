"""Public Click-based CLI for the validated Python surface of HIR."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Sequence

import click

from hir.core.network import enhanced_arp_scan, get_vendor_from_mac, hybrid_os_fingerprint
from hir.core.ping import ping_host
from hir.core.traceroute import traceroute_host
from hir.output.html import render_html
from hir.output.json import dump_json

_HELP_CONTEXT = {"help_option_names": ["-h", "--help"]}


def _format_os_guess(raw_os: str | None) -> str:
    """Return an honest user-facing OS label for heuristic fingerprints."""
    if not raw_os or raw_os == "Desconocido":
        return "Sin datos suficientes"
    return f"Posible {raw_os} (heurístico)"


def _slugify(value: str) -> str:
    safe = "".join(char if char.isalnum() else "_" for char in value.strip())
    return safe.strip("_") or "report"


def _export_report(
    data: dict[str, Any],
    output_format: str,
    base_filename: str,
    output_dir: Path | None = None,
) -> str | None:
    """Export report data through the existing JSON or HTML backends."""
    if output_format == "console":
        return None

    if output_format == "json":
        directory = str(output_dir) if output_dir is not None else "results/json"
        return dump_json(data, base_filename=base_filename, directory=directory)

    directory = str(output_dir) if output_dir is not None else "results/html"
    return render_html(data, base_filename=base_filename, directory=directory)


def _format_rtt(value: float) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.2f} ms"


def _validate_export_options(output_format: str, output_dir: Path | None) -> None:
    if output_format == "console" and output_dir is not None:
        raise click.UsageError("--output-dir is only valid when exporting JSON or HTML.")


def _is_privilege_error(exc: BaseException) -> bool:
    if isinstance(exc, PermissionError):
        return True

    if isinstance(exc, OSError) and exc.errno in {1, 13}:
        return True

    message = str(exc).lower()
    return any(
        hint in message
        for hint in (
            "operation not permitted",
            "permission denied",
            "not permitted",
            "cannot set filter",
        )
    )


def _build_ping_report(host: str, count: int, timeout: int) -> dict[str, Any]:
    rtt_values = ping_host(host, count=count, timeout=timeout)
    summary: dict[str, Any] = {
        "host": host,
        "count": count,
        "timeout": timeout,
        "rtt_ms": rtt_values,
        "received": len(rtt_values),
    }

    if rtt_values:
        summary["min_ms"] = min(rtt_values)
        summary["avg_ms"] = sum(rtt_values) / len(rtt_values)
        summary["max_ms"] = max(rtt_values)
    else:
        summary["min_ms"] = None
        summary["avg_ms"] = None
        summary["max_ms"] = None

    return summary


def _build_traceroute_report(host: str, max_hops: int, timeout: int) -> dict[str, Any]:
    return {
        "host": host,
        "max_hops": max_hops,
        "timeout": timeout,
        "hops": traceroute_host(host, max_hops=max_hops, timeout=timeout),
    }


def _build_arp_report(subnet: str, timeout: int) -> dict[str, Any]:
    try:
        devices = enhanced_arp_scan(subnet, timeout=timeout)
    except Exception as exc:
        if _is_privilege_error(exc):
            raise click.ClickException(
                "ARP scan requires root privileges or raw-socket capabilities "
                "(CAP_NET_RAW/CAP_NET_ADMIN). Re-run with sudo or grant the "
                "required capabilities to the Python environment."
            ) from exc
        raise click.ClickException(f"ARP scan failed: {exc}") from exc

    normalized_devices: list[dict[str, str]] = []
    for device in devices:
        normalized_device = dict(device)
        normalized_device["vendor"] = get_vendor_from_mac(device["mac"])
        try:
            raw_os = hybrid_os_fingerprint(device["ip"])
        except Exception:
            raw_os = None
        normalized_device["os"] = _format_os_guess(raw_os)
        normalized_devices.append(normalized_device)

    return {
        "subnet": subnet,
        "timeout": timeout,
        "devices": normalized_devices,
        "os_note": "El sistema operativo mostrado es una estimación heurística.",
    }


def _load_report_data(report_path: Path) -> dict[str, Any]:
    try:
        raw_data = json.loads(report_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise click.ClickException(f"Unable to read report file: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Report file is not valid JSON: {report_path}") from exc

    if not isinstance(raw_data, dict):
        raise click.ClickException("Report file must contain a top-level JSON object.")

    if "hops" in raw_data and "host" in raw_data:
        return raw_data
    if "devices" in raw_data and "subnet" in raw_data:
        return raw_data

    raise click.ClickException(
        "Unsupported report type. report-export only accepts traceroute or arp-scan JSON exports."
    )


@click.group(context_settings=_HELP_CONTEXT)
def cli() -> None:
    """HIR network diagnostics for the validated Python workflow."""


@cli.command("ping")
@click.argument("host")
@click.option("--count", default=4, show_default=True, type=click.IntRange(min=1))
@click.option("--timeout", default=2, show_default=True, type=click.IntRange(min=1))
@click.option(
    "--format",
    "output_format",
    default="console",
    show_default=True,
    type=click.Choice(["console", "json"], case_sensitive=False),
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Directory used for JSON exports.",
)
def ping_command(host: str, count: int, timeout: int, output_format: str, output_dir: Path | None) -> None:
    """Run ICMP ping against HOST."""
    _validate_export_options(output_format, output_dir)

    try:
        report = _build_ping_report(host, count=count, timeout=timeout)
    except (RuntimeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    if output_format == "console":
        click.echo(f"Ping report for {report['host']}")
        click.echo(f"Sent: {report['count']}  Received: {report['received']}")
        if report["received"]:
            click.echo(
                "RTT ms: "
                f"min={report['min_ms']:.2f} "
                f"avg={report['avg_ms']:.2f} "
                f"max={report['max_ms']:.2f}"
            )
        else:
            click.echo("No ICMP replies were parsed from ping output.")
        return

    report_path = _export_report(
        report,
        output_format=output_format,
        base_filename=f"ping_{_slugify(host)}",
        output_dir=output_dir,
    )
    click.echo(report_path)


@cli.command("traceroute")
@click.argument("host")
@click.option("--max-hops", default=30, show_default=True, type=click.IntRange(min=1))
@click.option("--timeout", default=2, show_default=True, type=click.IntRange(min=1))
@click.option(
    "--format",
    "output_format",
    default="console",
    show_default=True,
    type=click.Choice(["console", "json", "html"], case_sensitive=False),
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Directory used for JSON or HTML exports.",
)
def traceroute_command(
    host: str,
    max_hops: int,
    timeout: int,
    output_format: str,
    output_dir: Path | None,
) -> None:
    """Run traceroute against HOST."""
    _validate_export_options(output_format, output_dir)

    try:
        report = _build_traceroute_report(host, max_hops=max_hops, timeout=timeout)
    except (RuntimeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    if output_format == "console":
        click.echo(f"Traceroute report for {report['host']}")
        if not report["hops"]:
            click.echo("No hops were parsed from traceroute output.")
            return

        for hop, ip, rtt in report["hops"]:
            click.echo(f"{hop:>2}  {ip:<15}  {_format_rtt(rtt)}")
        return

    report_path = _export_report(
        report,
        output_format=output_format,
        base_filename=f"traceroute_{_slugify(host)}",
        output_dir=output_dir,
    )
    click.echo(report_path)


@cli.command("arp-scan")
@click.argument("subnet")
@click.option("--timeout", default=1, show_default=True, type=click.IntRange(min=1))
@click.option(
    "--format",
    "output_format",
    default="console",
    show_default=True,
    type=click.Choice(["console", "json", "html"], case_sensitive=False),
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Directory used for JSON or HTML exports.",
)
def arp_scan_command(subnet: str, timeout: int, output_format: str, output_dir: Path | None) -> None:
    """Run an ARP scan against SUBNET."""
    _validate_export_options(output_format, output_dir)

    report = _build_arp_report(subnet, timeout=timeout)

    if output_format == "console":
        click.echo(f"ARP scan report for {report['subnet']}")
        click.echo("OS results are heuristic guesses based on available network signals.")
        if not report["devices"]:
            click.echo("No devices were discovered.")
            return

        header = f"{'IP':<15} {'MAC':<17} {'Vendor':<20} Heuristic OS guess"
        click.echo(header)
        for device in report["devices"]:
            click.echo(
                f"{device['ip']:<15} {device['mac']:<17} "
                f"{device['vendor']:<20} {device['os']}"
            )
        return

    report_path = _export_report(
        report,
        output_format=output_format,
        base_filename=f"arp_scan_{_slugify(subnet)}",
        output_dir=output_dir,
    )
    click.echo(report_path)


@cli.command("report-export")
@click.argument("report_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Directory used for HTML exports.",
)
@click.option(
    "--base-filename",
    default=None,
    help="Optional base filename for the generated HTML report.",
)
def report_export_command(report_path: Path, output_dir: Path | None, base_filename: str | None) -> None:
    """Render a supported JSON report to HTML."""
    report = _load_report_data(report_path)
    html_path = render_html(
        report,
        base_filename=base_filename or report_path.stem,
        directory=str(output_dir) if output_dir is not None else "results/html",
    )
    click.echo(html_path)


def main(args: Sequence[str] | None = None) -> None:
    """Run the HIR CLI entry point."""
    cli.main(args=list(args) if args is not None else None, prog_name="hir")


if __name__ == "__main__":
    main()
