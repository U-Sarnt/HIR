# HIR Architecture

This document describes the internal architecture of HIR after the phase 3 cleanup. It focuses on the validated public workflow:

- `hir ping`
- `hir traceroute`
- `hir arp-scan`
- `hir report-export`

The goal of this layout is maintainability, not feature expansion. Public CLI behavior remains intentionally narrow.

## Layout

```text
src/hir/
  cli.py
  core/
    __init__.py
    arp.py
    errors.py
    fingerprint.py
    models.py
    network.py
    ping.py
    traceroute.py
    vendor.py
  output/
    __init__.py
    console.py
    files.py
    html.py
    json.py
    templates/
```

## Module Responsibilities

### CLI layer

- `src/hir/cli.py`
  - owns the Click command surface and help text
  - validates CLI-only option combinations
  - calls one internal use-case function per command
  - delegates rendering/export to the output layer
  - translates internal `HIRError` exceptions into stable Click failures

The CLI should not contain discovery logic, parsing logic, or template/file output details.

### Core logic

- `src/hir/core/ping.py`
  - builds and runs the system `ping` command
  - parses ICMP reply lines
  - returns `PingResult`

- `src/hir/core/traceroute.py`
  - builds and runs the system `traceroute` command
  - parses hop lines into `TracerouteHop`
  - returns `TracerouteResult`

- `src/hir/core/arp.py`
  - performs ARP discovery through Scapy
  - normalizes privilege failures into `PrivilegeRequiredError`
  - coordinates best-effort enrichment for ARP results
  - returns `ArpScanResult`

- `src/hir/core/vendor.py`
  - loads the optional OUI data source
  - resolves MAC prefixes to vendor labels

- `src/hir/core/fingerprint.py`
  - contains best-effort OS fingerprint heuristics
  - keeps heuristic probes isolated from CLI and rendering code

- `src/hir/core/models.py`
  - defines lightweight dataclasses for validated report shapes
  - centralizes JSON-compatible conversion and supported-report parsing

- `src/hir/core/errors.py`
  - defines the explicit internal error model

- `src/hir/core/network.py`
  - compatibility facade for legacy imports
  - no longer owns the main implementation paths
  - still contains the older `port_scan` helper, which remains outside the validated workflow

### Output layer

- `src/hir/output/console.py`
  - renders console output for ping, traceroute, and ARP results

- `src/hir/output/json.py`
  - writes JSON exports
  - loads supported exported reports for `report-export`

- `src/hir/output/html.py`
  - selects the appropriate HTML template
  - builds rendering context for traceroute and ARP reports
  - renders HTML exports only

- `src/hir/output/files.py`
  - handles sequential output filenames
  - applies the current file permission/ownership behavior

- `src/hir/output/templates/`
  - contains bundled Jinja2 templates shipped with the package

## System-Facing Boundaries

HIR currently touches the host system in a few explicit places:

- `core/ping.py`: system `ping`
- `core/traceroute.py`: system `traceroute`
- `core/arp.py`: Scapy raw-socket ARP discovery
- `core/fingerprint.py`: optional heuristic subprocess and packet probes
- `core/vendor.py`: optional packaged/local OUI file loading
- `output/files.py`: file creation, chmod, and optional chown for exported reports

Keeping these integrations easy to spot makes future testing and portability work simpler.

## Data and Error Boundaries

The main command results are represented with dataclasses:

- `PingResult`
- `TracerouteHop`
- `TracerouteResult`
- `ArpHost`
- `ArpScanResult`

Expected failures use explicit exceptions instead of vague generic ones:

- `HIRError`
- `DependencyMissingError`
- `PrivilegeRequiredError`
- `ParseError`
- `ReportExportError`
- `CommandExecutionError`

This gives the CLI and future tests a clearer contract.

## Architectural Principles

- Keep `cli.py` thin. Click commands should orchestrate, not implement diagnostics.
- Keep domain logic close to the system integration it depends on.
- Keep rendering and export logic in `hir.output`, not in the discovery modules.
- Use typed dataclasses at module boundaries when a command returns structured data.
- Prefer explicit exceptions for expected operational failures.
- Preserve the validated public workflow before adding broader abstractions.
- Avoid catch-all utility modules unless the helpers are truly shared and cohesive.

## Guidance for Future Contributors

- Add new command behavior by introducing or extending a domain module under `hir.core`, then wiring it through `hir.cli`.
- Add new export behavior under `hir.output`; do not mix template/file logic into CLI or probe code.
- If a legacy shim such as `core/network.py` is still needed, keep it thin and avoid putting new feature logic there.
- Treat heuristic enrichment as optional and best-effort. Do not present it as validated ground truth.
- Keep packaging assumptions intact: templates remain package data, and the `hir` entry point remains `hir.cli:main`.
