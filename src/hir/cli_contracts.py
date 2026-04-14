"""Stable CLI-facing exit codes and Click exceptions."""

from __future__ import annotations

from enum import IntEnum

import click


class ExitCode(IntEnum):
    """Stable process exit codes for the public CLI surface."""

    SUCCESS = 0
    OPERATIONAL_ERROR = 1
    USAGE_ERROR = 2


class CLIUsageError(click.UsageError):
    """Usage or argument validation error with a stable exit code."""

    exit_code = int(ExitCode.USAGE_ERROR)


class CLIOperationalError(click.ClickException):
    """Expected runtime failure with a stable exit code."""

    exit_code = int(ExitCode.OPERATIONAL_ERROR)
