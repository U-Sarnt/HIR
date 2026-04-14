"""Public Click-based CLI for the validated Python surface of HIR."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import click

from hir.cli_contracts import CLIOperationalError, CLIUsageError, ExitCode
from hir.core.arp import run_arp_scan
from hir.core.errors import HIRError
from hir.core.models import ArpScanResult, PingResult, TracerouteResult
from hir.core.ping import run_ping
from hir.core.traceroute import run_traceroute
from hir.output.console import (
    render_arp_console,
    render_ping_console,
    render_traceroute_console,
)
from hir.output.files import normalize_output_base_filename
from hir.output.html import render_html
from hir.output.json import dump_json, load_report

_HELP_CONTEXT = {"help_option_names": ["-h", "--help"], "max_content_width": 100}

CoreReport = PingResult | TracerouteResult | ArpScanResult


def _slugify(value: str) -> str:
    safe = "".join(char if char.isalnum() else "_" for char in value.strip())
    return safe.strip("_") or "report"


def _validate_export_options(output_format: str, output_dir: Path | None) -> None:
    if output_format == "console" and output_dir is not None:
        raise CLIUsageError(
            "--output-dir can only be used with --format json or --format html."
        )


def _export_report(
    report: CoreReport,
    *,
    output_format: str,
    base_filename: str,
    output_dir: Path | None = None,
) -> str | None:
    if output_format == "console":
        return None

    if output_format == "json":
        directory = output_dir if output_dir is not None else Path("results/json")
        return dump_json(report, base_filename=base_filename, directory=directory)

    if isinstance(report, PingResult):
        raise ValueError("HTML export is only supported for traceroute and ARP reports.")

    directory = output_dir if output_dir is not None else Path("results/html")
    return render_html(report, base_filename=base_filename, directory=directory)


@click.group(context_settings=_HELP_CONTEXT)
def cli() -> None:
    """Conservative network diagnostics for shell use and automation.

    Command results are written to stdout. Usage errors and runtime failures are written to stderr.
    """


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
    help=(
        "Output mode. Console prints the report to stdout. "
        "JSON writes a file and prints its path."
    ),
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Destination directory for JSON exports.",
)
def ping_command(
    host: str,
    count: int,
    timeout: int,
    output_format: str,
    output_dir: Path | None,
) -> None:
    """Run ICMP ping against HOST."""
    _validate_export_options(output_format, output_dir)

    try:
        report = run_ping(host, count=count, timeout=timeout)
    except (HIRError, ValueError) as exc:
        raise CLIOperationalError(str(exc)) from exc

    if output_format == "console":
        click.echo(render_ping_console(report))
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
    help="Output mode. Console prints the report. JSON or HTML write a file and print its path.",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Destination directory for JSON or HTML exports.",
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
        report = run_traceroute(host, max_hops=max_hops, timeout=timeout)
    except (HIRError, ValueError) as exc:
        raise CLIOperationalError(str(exc)) from exc

    if output_format == "console":
        click.echo(render_traceroute_console(report))
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
    help="Output mode. Console prints the report. JSON or HTML write a file and print its path.",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Destination directory for JSON or HTML exports.",
)
def arp_scan_command(
    subnet: str,
    timeout: int,
    output_format: str,
    output_dir: Path | None,
) -> None:
    """Run an ARP scan against SUBNET."""
    _validate_export_options(output_format, output_dir)

    try:
        report = run_arp_scan(subnet, timeout=timeout)
    except (HIRError, ValueError) as exc:
        raise CLIOperationalError(str(exc)) from exc

    if output_format == "console":
        click.echo(render_arp_console(report))
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
    help="Destination directory for HTML exports.",
)
@click.option(
    "--base-filename",
    default=None,
    help="Optional base filename. HIR adds the numeric suffix automatically.",
)
def report_export_command(
    report_path: Path,
    output_dir: Path | None,
    base_filename: str | None,
) -> None:
    """Render a supported JSON report to HTML."""
    try:
        report = load_report(report_path)
        html_path = render_html(
            report,
            base_filename=base_filename or normalize_output_base_filename(report_path.stem),
            directory=output_dir if output_dir is not None else Path("results/html"),
        )
    except HIRError as exc:
        raise CLIOperationalError(str(exc)) from exc

    click.echo(html_path)


def _run_cli(args: Sequence[str] | None = None) -> int:
    """Run the HIR CLI and return the stable process exit code."""
    argv = list(args) if args is not None else None

    try:
        cli.main(args=argv, prog_name="hir", standalone_mode=False)
    except click.exceptions.Exit as exc:
        return exc.exit_code
    except click.ClickException as exc:
        exc.show()
        return exc.exit_code
    except click.Abort:
        click.echo("Aborted.", err=True)
        return int(ExitCode.OPERATIONAL_ERROR)

    return int(ExitCode.SUCCESS)


def main(args: Sequence[str] | None = None) -> None:
    """Run the HIR CLI entry point."""
    raise SystemExit(_run_cli(args))


if __name__ == "__main__":
    main()
