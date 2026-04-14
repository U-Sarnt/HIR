"""HIR plugin foundation introduced in phase 6."""

from hir.plugins.contracts import (
    PLUGIN_API_VERSION,
    PLUGIN_ENTRY_POINT_GROUP,
    AcquisitionProvider,
    CapabilityKind,
    CapabilityRecord,
    HIRPlugin,
    OSFingerprintProvider,
    OutputHandler,
    OutputRequest,
    PluginMetadata,
    ReportLoader,
    VendorResolver,
)
from hir.plugins.discovery import PluginDiscoveryResult, PluginLoadFailure, discover_plugins
from hir.plugins.registry import PluginRegistry
from hir.plugins.runtime import (
    get_plugin_runtime,
    get_runtime_discovery_failures,
    get_runtime_registry,
    reset_plugin_runtime,
)

__all__ = [
    "AcquisitionProvider",
    "CapabilityKind",
    "CapabilityRecord",
    "HIRPlugin",
    "OSFingerprintProvider",
    "OutputHandler",
    "OutputRequest",
    "PLUGIN_API_VERSION",
    "PLUGIN_ENTRY_POINT_GROUP",
    "PluginDiscoveryResult",
    "PluginLoadFailure",
    "PluginMetadata",
    "PluginRegistry",
    "ReportLoader",
    "VendorResolver",
    "discover_plugins",
    "get_plugin_runtime",
    "get_runtime_discovery_failures",
    "get_runtime_registry",
    "reset_plugin_runtime",
]
