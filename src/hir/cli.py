"""Public Click-based CLI for the validated Python surface of HIR."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, cast

import click

from hir.cli_contracts import CLIOperationalError, CLIUsageError, ExitCode
from hir.core.errors import HIRError
from hir.core.models import ArpScanResult, PingResult, TracerouteResult
from hir.output.contracts import report_type_for_report
from hir.output.files import normalize_output_base_filename
from hir.plugins.contracts import OutputRequest
from hir.plugins.runtime import get_runtime_registry

_HELP_CONTEXT = {"help_option_names": ["-h", "--help"], "max_content_width": 100}

CoreReport = PingResult | TracerouteResult | ArpScanResult


def _slugify(value: str) -> str:
    safe = "".join(char if char.isalnum() else "_" for char in value.strip())
    return safe.strip("_") or "report"


def _validate_export_options(
    report_type: str,
    output_format: str,
    output_dir: Path | None,
) -> None:
    if output_dir is None:
        return

    handler = get_runtime_registry().get_output_handler(output_format, report_type)
    if handler.destination == "stdout":
        raise CLIUsageError(
            "--output-dir can only be used with --format json or --format html."
        )


def _run_provider(name: str, **kwargs: object) -> object:
    provider = get_runtime_registry().get_acquisition_provider(name)
    return provider.runner(**kwargs)


def _dispatch_output(
    report: CoreReport,
    *,
    report_type: str,
    output_format: str,
    base_filename: str,
    output_dir: Path | None = None,
) -> str | None:
    handler = get_runtime_registry().get_output_handler(output_format, report_type)
    return handler.handler(
        report,
        OutputRequest(base_filename=base_filename, output_dir=output_dir),
    )


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
    _validate_export_options("ping", output_format, output_dir)

    try:
        report = cast(
            PingResult,
            _run_provider("ping", host=host, count=count, timeout=timeout),
        )
    except (HIRError, ValueError) as exc:
        raise CLIOperationalError(str(exc)) from exc

    rendered = _dispatch_output(
        report,
        report_type="ping",
        output_format=output_format,
        base_filename=f"ping_{_slugify(host)}",
        output_dir=output_dir,
    )
    if rendered is not None:
        click.echo(rendered)


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
    _validate_export_options("traceroute", output_format, output_dir)

    try:
        report = cast(
            TracerouteResult,
            _run_provider(
                "traceroute",
                host=host,
                max_hops=max_hops,
                timeout=timeout,
            ),
        )
    except (HIRError, ValueError) as exc:
        raise CLIOperationalError(str(exc)) from exc

    rendered = _dispatch_output(
        report,
        report_type="traceroute",
        output_format=output_format,
        base_filename=f"traceroute_{_slugify(host)}",
        output_dir=output_dir,
    )
    if rendered is not None:
        click.echo(rendered)


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
    _validate_export_options("arp-scan", output_format, output_dir)

    try:
        report = cast(
            ArpScanResult,
            _run_provider("arp-scan", subnet=subnet, timeout=timeout),
        )
    except (HIRError, ValueError) as exc:
        raise CLIOperationalError(str(exc)) from exc

    rendered = _dispatch_output(
        report,
        report_type="arp-scan",
        output_format=output_format,
        base_filename=f"arp_scan_{_slugify(subnet)}",
        output_dir=output_dir,
    )
    if rendered is not None:
        click.echo(rendered)


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
        report = cast(CoreReport, get_runtime_registry().load_report(report_path))
        html_path = _dispatch_output(
            report,
            report_type=report_type_for_report(report),
            output_format="html",
            base_filename=base_filename or normalize_output_base_filename(report_path.stem),
            output_dir=output_dir,
        )
    except HIRError as exc:
        raise CLIOperationalError(str(exc)) from exc

    if html_path is not None:
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
