# HIR

HIR is an early-stage Python CLI for conservative network diagnostics and report export. The project is intentionally narrow at this stage: it focuses on a small validated command surface, explicit operational limits, and outputs that are suitable for shell use and simple automation.

## What HIR Is

HIR is a Python-first command-line tool for running a small set of common network diagnostics and exporting the resulting data. The current public contract is the validated CLI surface described in this README.

Internally, HIR now also includes a conservative plugin and capability registry for acquisition, output handling, report loading, and enrichment. That foundation is meant to improve maintainability and future growth; it does not change the intentionally narrow public CLI.

## Project Philosophy

- Conservative: HIR favors standard diagnostics, clear privilege requirements, and modest scope over aggressive scanning or broad claims.
- Evidence-oriented: HIR distinguishes measured results from heuristic enrichment and avoids presenting guesses as verified facts.
- Automation-friendly: HIR keeps the public workflow CLI-based, scriptable, and able to export structured results.

## Validated Scope Today

- `hir ping HOST` runs ICMP ping through the system `ping` binary and supports console or JSON output.
- `hir traceroute HOST` runs traceroute through the system `traceroute` binary and supports console, JSON, or HTML output.
- `hir arp-scan SUBNET` performs local ARP discovery with Scapy and supports console, JSON, or HTML output.
- `hir report-export REPORT.json` renders supported JSON reports to HTML. Supported inputs today are `traceroute` and `arp-scan` JSON exports.

## Current Limits

- HIR is early-stage and should be treated as a narrow CLI utility, not as a broad network platform.
- The validated workflow today is Python-first and Linux-oriented. `ping` and `traceroute` must be available in `PATH` and compatible with the flags HIR uses.
- `hir arp-scan` requires root privileges or equivalent raw-socket capabilities such as `CAP_NET_RAW` or `CAP_NET_ADMIN`.
- Ping can export JSON, but HTML rendering is currently limited to traceroute and ARP reports.
- ARP output may include vendor labels and operating system guesses, but those fields are not part of the validated diagnostic core.
- The plugin foundation is currently aimed at maintainers and controlled extensions, not at a broad public plugin ecosystem.

## Experimental or Not Yet Guaranteed

- Operating system identification is heuristic and should not be treated as validated fingerprinting.
- MAC vendor enrichment is best-effort and may be unavailable depending on packaged data and local tooling.
- Any workflow outside the validated CLI surface, including third-party command plugins or Rust-based acceleration, is not yet a guaranteed public path.

## What HIR Is Not

- HIR is not a replacement for mature network discovery, asset inventory, or vulnerability scanning suites.
- HIR is not an aggressive scanner, stealth tool, or high-speed enumeration framework.
- HIR is not a broad plugin marketplace or multi-language architecture.

## Installation

HIR currently targets Python 3.10 or newer.

Prerequisites for live diagnostics:

- `ping` available in `PATH`
- `traceroute` available in `PATH`
- raw-socket privileges for `hir arp-scan` if you plan to run live ARP discovery

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

For local development, use `pip install -e ".[dev]"`.

Packaging and release instructions live in [docs/PACKAGING_AND_RELEASES.md](docs/PACKAGING_AND_RELEASES.md).

## CLI usage

```bash
hir --help
hir ping 1.1.1.1
hir ping 1.1.1.1 --format json
hir traceroute example.com --format html
sudo "$(command -v hir)" arp-scan 192.168.1.0/24 --format json
hir report-export results/json/traceroute_example_com_01.json
```

JSON and HTML exports print the generated file path to standard output. By default, exported files are written under `results/json` or `results/html`.
Usage and runtime errors are written to standard error. The versioned JSON contract is documented in [docs/CLI_OUTPUT_CONTRACTS.md](docs/CLI_OUTPUT_CONTRACTS.md).

## Recommended Validation

On a clean Linux environment, validate the documented path with:

```bash
python -m pip install -e ".[dev]"
hir --help
hir ping --help
hir traceroute --help
hir arp-scan --help
hir report-export --help
python -m pytest -q
hir ping 127.0.0.1
hir traceroute example.com --format json
```

If you want to validate live ARP discovery, run it only on a controlled subnet and with the required privileges:

```bash
sudo "$(command -v hir)" arp-scan 192.168.1.0/24 --format json
hir report-export results/json/arp_scan_192_168_1_0_24_01.json
```

## Project Documents

- [ROADMAP.md](ROADMAP.md) explains the staged direction of the project.
- [CONTRIBUTING.md](CONTRIBUTING.md) describes the current contributor workflow.
- [SECURITY.md](SECURITY.md) explains how to report vulnerabilities.
- [docs/PROJECT_POSITIONING.md](docs/PROJECT_POSITIONING.md) summarizes the public positioning.
- [docs/PHASE1_SUMMARY.md](docs/PHASE1_SUMMARY.md) records what phase 1 changed and what remains deferred.
- [docs/PHASE2_SUMMARY.md](docs/PHASE2_SUMMARY.md) records packaging and release work from phase 2.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) describes the current internal layout after the phase 3 cleanup.
- [docs/PHASE3_SUMMARY.md](docs/PHASE3_SUMMARY.md) summarizes the architecture refactor and remaining debt.
- [docs/QUALITY_ASSURANCE.md](docs/QUALITY_ASSURANCE.md) describes the current test, lint, typing, coverage, and CI gates.
- [docs/PHASE4_SUMMARY.md](docs/PHASE4_SUMMARY.md) records what phase 4 added and what quality debt remains.
- [docs/CLI_OUTPUT_CONTRACTS.md](docs/CLI_OUTPUT_CONTRACTS.md) defines the stdout/stderr rules, exit codes, and versioned JSON contract.
- [docs/PHASE5_SUMMARY.md](docs/PHASE5_SUMMARY.md) summarizes the CLI contract and output work completed in phase 5.
- [docs/PLUGIN_ARCHITECTURE.md](docs/PLUGIN_ARCHITECTURE.md) documents the current extensibility architecture and its deliberate limits.
- [docs/PHASE6_SUMMARY.md](docs/PHASE6_SUMMARY.md) summarizes the plugin foundation added in phase 6.

## License

MIT
