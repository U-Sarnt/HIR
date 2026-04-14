# HIR Plugin Architecture

HIR phase 6 introduces a conservative plugin foundation so the project can grow without turning the current CLI into a loose collection of hard-coded special cases.

The goal is internal extensibility first:

- make supported extension points explicit
- keep compatibility checks and registration rules simple
- keep builtin behavior visible and testable
- leave room for external plugins later without forcing a framework rewrite today

The current design is Python-first and intentionally small.

## Design Goals

- Preserve the validated CLI and output contracts from phase 5.
- Register builtin capabilities the same way future extensions are registered.
- Keep discovery sober: builtin plugins are explicit, third-party discovery is optional, and failures are traceable.
- Favor explicit types and registries over import-time magic.

## Runtime Layout

The plugin foundation lives in `src/hir/plugins/`:

- `contracts.py`
  - plugin metadata
  - capability descriptors
  - typed contracts for acquisition providers, output handlers, report loaders, vendor resolvers, and OS fingerprint providers
- `registry.py`
  - central `PluginRegistry`
  - uniqueness checks
  - capability catalog
  - lookup helpers for runtime resolution
- `discovery.py`
  - loads builtin plugins
  - optionally loads third-party plugins from Python entry points in the `hir.plugins` group
  - records non-fatal discovery failures unless strict mode is requested
- `runtime.py`
  - caches the discovered runtime registry
- `builtins.py`
  - registers the builtin HIR capabilities using the same contracts as future plugins

## Supported Extension Types

HIR currently supports these extension-point categories:

- `acquisition.provider`
  - executable providers for validated report-producing workflows
  - builtin providers: `ping`, `traceroute`, `arp-scan`
- `output.handler`
  - format/report-type handlers
  - builtin handlers: console, JSON, and HTML as supported by the current product surface
- `report.loader`
  - persisted-report loaders selected by file suffix
  - builtin loader: `.json`
- `enrichment.vendor_resolver`
  - MAC vendor lookup chain used by ARP enrichment
- `enrichment.os_fingerprint`
  - heuristic fingerprint providers used by ARP enrichment

## Not Supported Yet

These are deliberate limits of the current design:

- external CLI command or subcommand plugins are not supported yet
- the validated CLI still exposes only the builtin formats already stabilized in previous phases
- custom report models outside the current typed result set are not part of the public contract yet
- there is no hot reload, sandboxing layer, plugin configuration system, or plugin dependency graph

That is intentional. Phase 6 is a foundation phase, not a framework phase.

## Registration Model

Each plugin exposes:

- `PluginMetadata`
  - includes `name`, `version`, `api_version`, `description`, and whether the plugin is builtin
- `register(registry)`
  - called once during discovery
  - must register capabilities through typed registry methods

The registry validates:

- plugin API compatibility through `PLUGIN_API_VERSION`
- unique plugin names
- unique capability ownership where collisions would be ambiguous
  - example: two output handlers cannot claim the same `(format, report_type)` pair
  - example: two report loaders cannot claim the same suffix

## Discovery Strategy

HIR uses a hybrid strategy:

1. builtin plugins are registered explicitly from `hir.plugins.builtins`
2. third-party plugins may be discovered through Python entry points in the `hir.plugins` group

Why this strategy:

- builtins remain obvious in the source tree
- third-party discovery uses a standard Python packaging mechanism
- tests can exercise discovery without relying on filesystem scanning
- discovery failures can be inspected without breaking builtin functionality by default

Behavior on failures:

- builtin registration is required and should fail hard
- external plugin failures are collected as traceable discovery failures by default
- strict mode can raise `PluginDiscoveryError` immediately

## Capability Traceability

`PluginRegistry.list_plugins()` returns the registered plugin metadata.

`PluginRegistry.list_capabilities()` returns the capability catalog, including:

- capability kind
- owning plugin
- capability name
- report types, format, suffix, or priority metadata when relevant

This gives a clear runtime inventory without requiring CLI-specific introspection commands.

## Builtin Integration in Phase 6

The current builtin product flow now uses the registry in real execution paths:

- CLI command execution resolves acquisition providers through the runtime registry
- CLI output/export resolution uses output handlers from the runtime registry
- `hir report-export` resolves loaders by suffix through the runtime registry, then dispatches to the HTML output handler
- `hir.core.vendor.get_vendor_from_mac()` resolves through the registered vendor-resolver chain
- `hir.core.fingerprint.hybrid_os_fingerprint()` resolves through the registered OS fingerprint provider chain

This means the plugin architecture is not cosmetic: the builtin product now runs on top of the same capability contracts it documents.

## Adding a New Internal Extension

Internal additions should follow this workflow:

1. implement the concrete logic in the appropriate module
2. wrap it in one of the typed capability contracts from `hir.plugins.contracts`
3. register it from a builtin plugin in `hir.plugins.builtins`
4. add tests for registration and behavior
5. document any new supported capability or deliberate limit

Example sketch for a new vendor resolver:

```python
from hir import __version__
from hir.plugins.contracts import PluginMetadata, VendorResolver


class BuiltinVendorPlugin:
    metadata = PluginMetadata(
        name="hir.builtin.extra-vendor",
        version=__version__,
        description="Extra vendor resolver.",
        builtin=True,
    )

    def register(self, registry) -> None:
        registry.register_vendor_resolver(
            VendorResolver(
                name="lab-vendor-db",
                resolver=lookup_vendor,
                priority=20,
                description="Looks up vendors in an internal lab mapping.",
            )
        )
```

## External Plugin Path

Third-party plugins can target the entry point group `hir.plugins`.

Minimal packaging sketch:

```toml
[project.entry-points."hir.plugins"]
acme = "acme_hir_plugin:build_plugin"
```

The entry point may expose:

- a plugin object with `metadata` and `register()`
- or a zero-argument factory that returns such an object

External plugins should:

- keep `api_version` aligned with `hir.plugins.contracts.PLUGIN_API_VERSION`
- avoid colliding with builtin capability keys
- treat HIR's current typed reports and CLI behavior as the stable baseline

## Compatibility Decisions

- existing commands remain `hir ping`, `hir traceroute`, `hir arp-scan`, and `hir report-export`
- stdout/stderr routing, exit codes, and report document contracts remain unchanged
- builtin formats remain the current public CLI formats: `console`, `json`, `html` where already supported
- plugin discovery does not silently replace builtin behavior on key collisions
- third-party plugin load failures do not break builtin CLI execution by default

## Deferred by Design

Phase 6 deliberately does not include:

- Rust integration
- a command-plugin ecosystem
- arbitrary runtime module loading from directories
- a plugin settings layer
- validation for plugin-specific config files
- a broader public framework promise

The architecture is intentionally ready for growth, but it is not pretending that every future extension surface is already stable today.
