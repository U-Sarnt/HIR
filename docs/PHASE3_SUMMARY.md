# Phase 3 Summary

## Audit: Main Architectural Pain Points

- `src/hir/cli.py` mixed Click wiring with report construction, console formatting, export routing, JSON report loading, and ARP privilege handling.
- `src/hir/core/network.py` had become a catch-all module for ARP discovery, vendor lookup, fingerprinting, and unrelated socket scanning.
- Result shapes were mostly loose dictionaries and tuples, which made it harder to understand boundaries or extend behavior safely.
- Expected failures from subprocesses, report parsing, and privileged operations were surfaced through broad generic exceptions.
- JSON and HTML exporters duplicated sequential filename and file permission logic.
- Console rendering lived in the CLI layer instead of an output-focused module.

## What Was Refactored

- Split the overloaded network implementation into focused modules:
  - `core/arp.py`
  - `core/vendor.py`
  - `core/fingerprint.py`
- Added explicit dataclasses for the main validated result shapes:
  - `PingResult`
  - `TracerouteHop`
  - `TracerouteResult`
  - `ArpHost`
  - `ArpScanResult`
- Added an internal exception hierarchy for expected failures in core and export code.
- Reworked `cli.py` so Click commands primarily orchestrate use cases and delegate rendering/export work.
- Moved console output rendering into `output/console.py`.
- Centralized output file sequencing and permission handling in `output/files.py`.
- Kept `output/json.py` and `output/html.py` focused on serialization/rendering concerns.
- Reduced `core/network.py` to a compatibility facade instead of the main implementation home.

## Responsibilities Now Separated More Cleanly

- CLI entrypoints live in `src/hir/cli.py`.
- Discovery, subprocess execution, and parsing live under `src/hir/core/`.
- Result data contracts live in `src/hir/core/models.py`.
- Expected operational failures live in `src/hir/core/errors.py`.
- Console, JSON, and HTML rendering live under `src/hir/output/`.
- System-facing filesystem behavior is isolated in `src/hir/output/files.py`.

## Architectural Debt Still Remaining

- `src/hir/core/network.py` still exists as a compatibility layer and still carries the older `port_scan` helper, which is outside the validated command surface.
- Heuristic fingerprinting remains best-effort, Linux-oriented, and only lightly isolated from optional external tools.
- There is still no bundled OUI data source, so vendor enrichment remains optional and frequently unavailable.
- Type coverage is improved around the refactored paths, but the project is not yet running a dedicated static type checker.
- Tests were updated for the refactor, but the larger test and CI expansion is intentionally still deferred.

## What Phase 4 Should Tackle Next

- Expand test depth around the new architecture boundaries rather than only command-level behavior.
- Decide whether the compatibility shim in `core/network.py` and the legacy `port_scan` helper should be removed or given a clearer home.
- Tighten validation around exported report schemas and report backward-compatibility expectations.
- Introduce lightweight static analysis or type-checking once the current module boundaries settle.
- Revisit heuristic enrichment boundaries and optional runtime data packaging, especially for vendor lookup.
