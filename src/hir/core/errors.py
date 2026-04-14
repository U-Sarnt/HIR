"""Custom exception hierarchy for expected HIR failures."""

from __future__ import annotations


class HIRError(Exception):
    """Base exception for expected HIR runtime failures."""


class DependencyMissingError(HIRError):
    """Raised when a required system dependency is unavailable."""


class PrivilegeRequiredError(HIRError):
    """Raised when an operation needs elevated privileges or capabilities."""


class ParseError(HIRError):
    """Raised when HIR cannot parse command or report data."""


class ReportExportError(HIRError):
    """Raised when a supported report cannot be exported."""


class CommandExecutionError(HIRError):
    """Raised when a delegated system command fails."""
