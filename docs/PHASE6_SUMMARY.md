# Phase 6 Summary

Phase 6 adds a professional plugin and capability foundation to HIR without changing the validated CLI surface or turning the project into a framework.

## Delivered

- explicit plugin contracts under `src/hir/plugins/`
- capability registry with plugin metadata, compatibility checks, and collision validation
- builtin registration for acquisition providers, output handlers, report loaders, vendor resolvers, and OS fingerprint providers
- optional discovery of third-party plugins through Python entry points in the `hir.plugins` group
- traceable discovery failures and strict-mode discovery errors
- migration of builtin execution paths to the new registry for output resolution, report loading, and enrichment chains
- dedicated documentation for plugin architecture and deliberate limits
- regression tests for registration, discovery, invalid plugins, builtin behavior, and runtime compatibility

## Compatibility Decisions

- the public commands remain unchanged
- stdout/stderr behavior and exit codes remain the phase 5 contract
- JSON and HTML output behavior remain stable for the validated workflows
- builtin capabilities are now registered internally as plugins, but this is an internal architecture change rather than a public CLI expansion
- `report-export` still renders HTML for supported report types; it now resolves loaders through the registry
- third-party plugin failures are reported clearly without breaking builtin CLI behavior by default

## Deliberately Deferred

- external CLI command plugins
- new output formats exposed on the public CLI by default
- custom report-model ecosystems
- plugin configuration files or plugin dependency management
- Rust work or larger language/runtime changes

## Outcome

HIR can now grow through explicit, typed extension points instead of accreting more direct imports and command-specific branching. The architecture remains narrow, testable, and aligned with the project's conservative scope.
