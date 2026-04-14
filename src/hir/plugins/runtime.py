"""Cached runtime access for the current HIR plugin registry."""

from __future__ import annotations

from hir.plugins.discovery import PluginDiscoveryResult, PluginLoadFailure, discover_plugins
from hir.plugins.registry import PluginRegistry

_CACHED_RUNTIME: PluginDiscoveryResult | None = None


def get_plugin_runtime(*, force_reload: bool = False) -> PluginDiscoveryResult:
    """Return the cached plugin runtime, discovering it on first access."""
    global _CACHED_RUNTIME

    if force_reload or _CACHED_RUNTIME is None:
        _CACHED_RUNTIME = discover_plugins()

    return _CACHED_RUNTIME


def get_runtime_registry(*, force_reload: bool = False) -> PluginRegistry:
    """Return the active plugin registry."""
    return get_plugin_runtime(force_reload=force_reload).registry


def get_runtime_discovery_failures(*, force_reload: bool = False) -> tuple[PluginLoadFailure, ...]:
    """Return non-fatal discovery failures from the cached runtime."""
    return get_plugin_runtime(force_reload=force_reload).failures


def reset_plugin_runtime() -> None:
    """Clear the cached runtime. Intended for tests."""
    global _CACHED_RUNTIME
    _CACHED_RUNTIME = None

