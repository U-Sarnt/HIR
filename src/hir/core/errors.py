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


class PluginError(HIRError):
    """Base exception for plugin and extension-system failures."""


class PluginRegistrationError(PluginError):
    """Raised when a plugin or capability cannot be registered."""


class PluginCompatibilityError(PluginError):
    """Raised when a plugin targets an incompatible HIR plugin API."""


class PluginDiscoveryError(PluginError):
    """Raised when plugin discovery fails in strict mode."""


class PluginLookupError(PluginError):
    """Raised when a required capability is not available in the registry."""
