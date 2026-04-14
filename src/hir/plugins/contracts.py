"""Explicit contracts for HIR's plugin and capability foundation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

if TYPE_CHECKING:
    from hir.plugins.registry import PluginRegistry

PLUGIN_API_VERSION = 1
PLUGIN_ENTRY_POINT_GROUP = "hir.plugins"

OutputDestination = Literal["stdout", "file"]


class CapabilityKind(str, Enum):
    """Supported extension-point categories in the current HIR runtime."""

    ACQUISITION_PROVIDER = "acquisition.provider"
    OUTPUT_HANDLER = "output.handler"
    REPORT_LOADER = "report.loader"
    VENDOR_RESOLVER = "enrichment.vendor_resolver"
    OS_FINGERPRINT = "enrichment.os_fingerprint"


@dataclass(frozen=True, slots=True)
class PluginMetadata:
    """Minimal plugin metadata used for registration and compatibility checks."""

    name: str
    version: str
    api_version: int = PLUGIN_API_VERSION
    description: str = ""
    builtin: bool = False

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Plugin metadata requires a non-empty name.")
        if not self.version.strip():
            raise ValueError("Plugin metadata requires a non-empty version.")


@dataclass(frozen=True, slots=True)
class OutputRequest:
    """Shared output context passed to output handlers."""

    base_filename: str
    output_dir: Path | None = None


@dataclass(frozen=True, slots=True)
class CapabilityRecord:
    """Traceable description of one capability registered in the runtime."""

    plugin_name: str
    kind: CapabilityKind
    name: str
    description: str = ""
    report_types: tuple[str, ...] = ()
    output_format: str | None = None
    file_suffixes: tuple[str, ...] = ()
    destination: OutputDestination | None = None
    priority: int | None = None


AcquisitionRunner = Callable[..., object]
OutputHandlerCallable = Callable[[object, OutputRequest], str | None]
ReportLoaderCallable = Callable[[str | Path], object]
VendorResolverCallable = Callable[[str], str | None]
OSFingerprintCallable = Callable[[str], str | None]


@dataclass(frozen=True, slots=True)
class AcquisitionProvider:
    """Executable provider for one supported acquisition/report type."""

    name: str
    report_type: str
    runner: AcquisitionRunner = field(repr=False)
    description: str = ""


@dataclass(frozen=True, slots=True)
class OutputHandler:
    """Output capability for a report type and format pair."""

    name: str
    output_format: str
    report_types: tuple[str, ...]
    destination: OutputDestination
    handler: OutputHandlerCallable = field(repr=False)
    description: str = ""
    file_suffix: str | None = None
    default_directory: str | None = None


@dataclass(frozen=True, slots=True)
class ReportLoader:
    """Loader for persisted report files."""

    name: str
    suffixes: tuple[str, ...]
    supported_report_types: tuple[str, ...]
    loader: ReportLoaderCallable = field(repr=False)
    description: str = ""


@dataclass(frozen=True, slots=True)
class VendorResolver:
    """Resolver that may enrich a MAC address with a vendor label."""

    name: str
    resolver: VendorResolverCallable = field(repr=False)
    description: str = ""
    priority: int = 100


@dataclass(frozen=True, slots=True)
class OSFingerprintProvider:
    """Provider that may return a best-effort OS guess for a host."""

    name: str
    detector: OSFingerprintCallable = field(repr=False)
    description: str = ""
    priority: int = 100


@runtime_checkable
class HIRPlugin(Protocol):
    """Protocol implemented by builtin and external HIR plugins."""

    metadata: PluginMetadata

    def register(self, registry: "PluginRegistry") -> None:
        """Register one or more capabilities in the provided registry."""
