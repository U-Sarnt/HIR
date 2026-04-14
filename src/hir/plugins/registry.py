"""Capability registry for builtin and discovered HIR plugins."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from hir.core.errors import (
    PluginCompatibilityError,
    PluginLookupError,
    PluginRegistrationError,
)
from hir.plugins.contracts import (
    PLUGIN_API_VERSION,
    AcquisitionProvider,
    CapabilityKind,
    CapabilityRecord,
    HIRPlugin,
    OSFingerprintProvider,
    OutputHandler,
    PluginMetadata,
    ReportLoader,
    VendorResolver,
)


class PluginRegistry:
    """In-memory registry of plugins and the capabilities they contribute."""

    def __init__(self) -> None:
        self._plugins: dict[str, PluginMetadata] = {}
        self._capabilities: list[CapabilityRecord] = []
        self._acquisition_providers: dict[str, AcquisitionProvider] = {}
        self._output_handlers: dict[str, OutputHandler] = {}
        self._output_handler_index: dict[tuple[str, str], str] = {}
        self._report_loaders: dict[str, ReportLoader] = {}
        self._report_loader_suffixes: dict[str, str] = {}
        self._vendor_resolvers: dict[str, VendorResolver] = {}
        self._os_fingerprint_providers: dict[str, OSFingerprintProvider] = {}
        self._active_plugin_name: str | None = None
        self._active_rollbacks: list[Callable[[], None]] | None = None

    def register_plugin(self, plugin: HIRPlugin) -> None:
        """Validate and register a plugin plus its contributed capabilities."""
        metadata = getattr(plugin, "metadata", None)
        if not isinstance(metadata, PluginMetadata):
            raise PluginRegistrationError("Plugins must expose PluginMetadata as 'metadata'.")

        if metadata.api_version != PLUGIN_API_VERSION:
            raise PluginCompatibilityError(
                f"Plugin {metadata.name!r} targets API version {metadata.api_version}, "
                f"expected {PLUGIN_API_VERSION}."
            )

        if metadata.name in self._plugins:
            raise PluginRegistrationError(f"Plugin {metadata.name!r} is already registered.")

        register = getattr(plugin, "register", None)
        if not callable(register):
            raise PluginRegistrationError(f"Plugin {metadata.name!r} does not define register().")

        self._active_plugin_name = metadata.name
        self._active_rollbacks = []
        try:
            register(self)
        except Exception:
            self._rollback_active_plugin()
            raise
        finally:
            self._active_plugin_name = None
            self._active_rollbacks = None

        self._plugins[metadata.name] = metadata

    def register_acquisition_provider(self, provider: AcquisitionProvider) -> None:
        """Register an acquisition/report provider."""
        plugin_name, rollbacks = self._begin_capability_registration()
        if provider.name in self._acquisition_providers:
            raise PluginRegistrationError(
                f"Acquisition provider {provider.name!r} is already registered."
            )

        self._acquisition_providers[provider.name] = provider
        rollbacks.append(lambda: self._drop_acquisition_provider(provider.name))
        self._append_capability(
            CapabilityRecord(
                plugin_name=plugin_name,
                kind=CapabilityKind.ACQUISITION_PROVIDER,
                name=provider.name,
                description=provider.description,
                report_types=(provider.report_type,),
            )
        )

    def register_output_handler(self, handler: OutputHandler) -> None:
        """Register an output handler for one or more report types."""
        plugin_name, rollbacks = self._begin_capability_registration()
        if handler.name in self._output_handlers:
            raise PluginRegistrationError(f"Output handler {handler.name!r} is already registered.")

        normalized_format = handler.output_format.lower()
        collisions: list[tuple[str, str]] = []
        for report_type in handler.report_types:
            key = (normalized_format, report_type)
            if key in self._output_handler_index:
                collisions.append(key)

        if collisions:
            rendered = ", ".join(f"{fmt}/{report}" for fmt, report in collisions)
            raise PluginRegistrationError(f"Output handler collisions detected for {rendered}.")

        self._output_handlers[handler.name] = handler
        rollbacks.append(lambda: self._drop_output_handler(handler.name))
        registered_keys = []
        for report_type in handler.report_types:
            key = (normalized_format, report_type)
            self._output_handler_index[key] = handler.name
            registered_keys.append(key)

        rollbacks.append(lambda: self._drop_output_handler_keys(registered_keys))
        self._append_capability(
            CapabilityRecord(
                plugin_name=plugin_name,
                kind=CapabilityKind.OUTPUT_HANDLER,
                name=handler.name,
                description=handler.description,
                report_types=handler.report_types,
                output_format=normalized_format,
                destination=handler.destination,
                file_suffixes=(handler.file_suffix,) if handler.file_suffix else (),
            )
        )

    def register_report_loader(self, loader: ReportLoader) -> None:
        """Register a loader for persisted report files."""
        plugin_name, rollbacks = self._begin_capability_registration()
        if loader.name in self._report_loaders:
            raise PluginRegistrationError(f"Report loader {loader.name!r} is already registered.")

        normalized_suffixes = tuple(suffix.lower() for suffix in loader.suffixes)
        collisions = [
            suffix for suffix in normalized_suffixes if suffix in self._report_loader_suffixes
        ]
        if collisions:
            rendered = ", ".join(collisions)
            raise PluginRegistrationError(f"Report loader collisions detected for {rendered}.")

        self._report_loaders[loader.name] = loader
        rollbacks.append(lambda: self._drop_report_loader(loader.name))
        for suffix in normalized_suffixes:
            self._report_loader_suffixes[suffix] = loader.name
        rollbacks.append(lambda: self._drop_report_loader_suffixes(normalized_suffixes))
        self._append_capability(
            CapabilityRecord(
                plugin_name=plugin_name,
                kind=CapabilityKind.REPORT_LOADER,
                name=loader.name,
                description=loader.description,
                report_types=loader.supported_report_types,
                file_suffixes=normalized_suffixes,
            )
        )

    def register_vendor_resolver(self, resolver: VendorResolver) -> None:
        """Register a MAC vendor resolver."""
        plugin_name, rollbacks = self._begin_capability_registration()
        if resolver.name in self._vendor_resolvers:
            raise PluginRegistrationError(
                f"Vendor resolver {resolver.name!r} is already registered."
            )

        self._vendor_resolvers[resolver.name] = resolver
        rollbacks.append(lambda: self._drop_vendor_resolver(resolver.name))
        self._append_capability(
            CapabilityRecord(
                plugin_name=plugin_name,
                kind=CapabilityKind.VENDOR_RESOLVER,
                name=resolver.name,
                description=resolver.description,
                priority=resolver.priority,
            )
        )

    def register_os_fingerprint_provider(self, provider: OSFingerprintProvider) -> None:
        """Register an OS fingerprint provider."""
        plugin_name, rollbacks = self._begin_capability_registration()
        if provider.name in self._os_fingerprint_providers:
            raise PluginRegistrationError(
                f"OS fingerprint provider {provider.name!r} is already registered."
            )

        self._os_fingerprint_providers[provider.name] = provider
        rollbacks.append(lambda: self._drop_os_fingerprint_provider(provider.name))
        self._append_capability(
            CapabilityRecord(
                plugin_name=plugin_name,
                kind=CapabilityKind.OS_FINGERPRINT,
                name=provider.name,
                description=provider.description,
                priority=provider.priority,
            )
        )

    def list_plugins(self) -> tuple[PluginMetadata, ...]:
        """Return registered plugins sorted by name."""
        return tuple(sorted(self._plugins.values(), key=lambda metadata: metadata.name))

    def list_capabilities(self) -> tuple[CapabilityRecord, ...]:
        """Return a stable catalog of registered capabilities."""
        return tuple(
            sorted(
                self._capabilities,
                key=lambda capability: (
                    capability.kind.value,
                    capability.plugin_name,
                    capability.name,
                ),
            )
        )

    def get_acquisition_provider(self, name: str) -> AcquisitionProvider:
        """Return the acquisition provider registered under the given name."""
        try:
            return self._acquisition_providers[name]
        except KeyError as exc:
            raise PluginLookupError(f"No acquisition provider is registered as {name!r}.") from exc

    def get_output_handler(self, output_format: str, report_type: str) -> OutputHandler:
        """Return the output handler for the format/report-type pair."""
        key = (output_format.lower(), report_type)
        handler_name = self._output_handler_index.get(key)
        if handler_name is None:
            raise PluginLookupError(
                f"No output handler is registered for format {output_format!r} "
                f"and report type {report_type!r}."
            )
        return self._output_handlers[handler_name]

    def get_output_formats(self, report_type: str) -> tuple[str, ...]:
        """Return the registered output formats for the given report type."""
        formats: list[str] = []
        for output_format, registered_report_type in self._output_handler_index:
            if registered_report_type != report_type:
                continue
            if output_format not in formats:
                formats.append(output_format)
        return tuple(formats)

    def get_report_loader_for_path(self, report_path: str | Path) -> ReportLoader:
        """Return the report loader selected by file suffix."""
        suffix = Path(report_path).suffix.lower()
        if not suffix:
            raise PluginLookupError("No report loader is registered for files without a suffix.")

        loader_name = self._report_loader_suffixes.get(suffix)
        if loader_name is None:
            raise PluginLookupError(f"No report loader is registered for '*{suffix}' files.")

        return self._report_loaders[loader_name]

    def load_report(self, report_path: str | Path) -> object:
        """Load a persisted report using the registered loader for its suffix."""
        loader = self.get_report_loader_for_path(report_path)
        return loader.loader(report_path)

    def iter_vendor_resolvers(self) -> tuple[VendorResolver, ...]:
        """Return vendor resolvers ordered by priority."""
        return tuple(
            sorted(
                self._vendor_resolvers.values(),
                key=lambda resolver: (resolver.priority, resolver.name),
            )
        )

    def iter_os_fingerprint_providers(self) -> tuple[OSFingerprintProvider, ...]:
        """Return OS fingerprint providers ordered by priority."""
        return tuple(
            sorted(
                self._os_fingerprint_providers.values(),
                key=lambda provider: (provider.priority, provider.name),
            )
        )

    def _begin_capability_registration(self) -> tuple[str, list[Callable[[], None]]]:
        if self._active_plugin_name is None or self._active_rollbacks is None:
            raise PluginRegistrationError(
                "Capabilities can only be registered while a plugin is being registered."
            )
        return self._active_plugin_name, self._active_rollbacks

    def _append_capability(self, capability: CapabilityRecord) -> None:
        self._capabilities.append(capability)
        if self._active_rollbacks is None:
            raise PluginRegistrationError(
                "Capabilities can only be registered while a plugin is being registered."
            )
        self._active_rollbacks.append(self._drop_last_capability)

    def _rollback_active_plugin(self) -> None:
        if self._active_rollbacks is None:
            return
        for rollback in reversed(self._active_rollbacks):
            rollback()

    def _drop_acquisition_provider(self, name: str) -> None:
        self._acquisition_providers.pop(name, None)

    def _drop_output_handler(self, name: str) -> None:
        self._output_handlers.pop(name, None)

    def _drop_output_handler_keys(self, keys: list[tuple[str, str]]) -> None:
        for key in keys:
            self._output_handler_index.pop(key, None)

    def _drop_report_loader(self, name: str) -> None:
        self._report_loaders.pop(name, None)

    def _drop_report_loader_suffixes(self, suffixes: tuple[str, ...]) -> None:
        for suffix in suffixes:
            self._report_loader_suffixes.pop(suffix, None)

    def _drop_vendor_resolver(self, name: str) -> None:
        self._vendor_resolvers.pop(name, None)

    def _drop_os_fingerprint_provider(self, name: str) -> None:
        self._os_fingerprint_providers.pop(name, None)

    def _drop_last_capability(self) -> None:
        self._capabilities.pop()
