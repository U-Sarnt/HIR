"""Plugin discovery for builtin and optional external HIR extensions."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import EntryPoint, entry_points
from typing import cast

from hir.core.errors import PluginDiscoveryError, PluginRegistrationError
from hir.plugins.builtins import iter_builtin_plugins
from hir.plugins.contracts import PLUGIN_ENTRY_POINT_GROUP, HIRPlugin, PluginMetadata
from hir.plugins.registry import PluginRegistry


@dataclass(frozen=True, slots=True)
class PluginLoadFailure:
    """One non-fatal failure encountered during plugin discovery."""

    source: str
    plugin_name: str
    message: str


@dataclass(frozen=True, slots=True)
class PluginDiscoveryResult:
    """Final discovery result used by the runtime cache."""

    registry: PluginRegistry
    failures: tuple[PluginLoadFailure, ...]


def discover_plugins(
    *,
    include_entry_points: bool = True,
    strict: bool = False,
) -> PluginDiscoveryResult:
    """Discover builtin plugins and optional third-party entry-point plugins."""
    registry = PluginRegistry()
    for plugin in iter_builtin_plugins():
        registry.register_plugin(_coerce_plugin(plugin, source="builtin"))

    failures: list[PluginLoadFailure] = []
    if include_entry_points:
        for entry_point in _iter_plugin_entry_points():
            try:
                loaded = entry_point.load()
                plugin = _coerce_plugin(loaded, source=f"entry point {entry_point.name}")
                registry.register_plugin(plugin)
            except Exception as exc:
                failure = PluginLoadFailure(
                    source=PLUGIN_ENTRY_POINT_GROUP,
                    plugin_name=entry_point.name,
                    message=str(exc),
                )
                if strict:
                    raise PluginDiscoveryError(
                        f"Failed to load plugin entry point {entry_point.name!r}: {exc}"
                    ) from exc
                failures.append(failure)

    return PluginDiscoveryResult(registry=registry, failures=tuple(failures))


def _iter_plugin_entry_points() -> tuple[EntryPoint, ...]:
    discovered = entry_points()
    if hasattr(discovered, "select"):
        return tuple(discovered.select(group=PLUGIN_ENTRY_POINT_GROUP))
    legacy = discovered.get(PLUGIN_ENTRY_POINT_GROUP, ())
    return tuple(legacy)


def _coerce_plugin(candidate: object, *, source: str) -> HIRPlugin:
    if _looks_like_plugin(candidate):
        return cast(HIRPlugin, candidate)

    if callable(candidate):
        built = candidate()
        if _looks_like_plugin(built):
            return cast(HIRPlugin, built)

    raise PluginRegistrationError(f"{source} did not provide a valid HIR plugin object.")


def _looks_like_plugin(candidate: object) -> bool:
    metadata = getattr(candidate, "metadata", None)
    register = getattr(candidate, "register", None)
    return isinstance(metadata, PluginMetadata) and callable(register)
