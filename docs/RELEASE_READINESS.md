# Release Readiness

## What "Release-Ready" Means for HIR

HIR is release-ready when it meets a narrow, explicit baseline:

- the packaged wheel and sdist build successfully from the repository state
- metadata, public version, CLI entry points, and bundled templates are consistent
- the validated CLI contract from phases 5 and 6 still works after a clean install
- support boundaries, privilege requirements, and best-effort areas are documented clearly
- release notes and compatibility expectations are updated together with the code

Release-ready does not mean broad platform support, plugin-marketplace maturity, or full live
integration coverage across every network environment.

## Current Release Posture

- Public package version: `0.1.0`
- Single source of truth for versioning: `hir.__version__`
- Validated public CLI surface: `ping`, `traceroute`, `arp-scan`, `report-export`
- Runtime orientation: Python-first, Linux-first, conservative diagnostics only
- Plugin posture: builtin extensibility base is maintained; a broad third-party plugin ecosystem is
  still best-effort and intentionally constrained

## Compatibility and Deprecation Policy

- HIR preserves the validated CLI contract within a release line unless a bug, safety issue, or
  explicit compatibility decision requires otherwise.
- Any intentional incompatible CLI, schema, or packaging change must be documented in
  `CHANGELOG.md` and the relevant docs before release.
- JSON contract changes must continue to use explicit schema versioning as documented in
  `docs/CLI_OUTPUT_CONTRACTS.md`.
- Deprecations should be introduced in documentation and release notes before removal whenever
  feasible. Silent removals are not the default path.
- The plugin API remains intentionally narrow. If an incompatible plugin change is needed, the
  change must be reflected through `PLUGIN_API_VERSION` and release notes.

## Release Validation Checklist

Run the full validation sequence before tagging or publishing:

```bash
python -m pip install -e ".[dev]"
python -m ruff check src tests
python -m mypy
python -m pytest -q
rm -rf dist/
python -m build
python -m twine check dist/*
```

Validate the wheel in a clean environment:

```bash
python -m venv /tmp/hir-wheel-smoke
. /tmp/hir-wheel-smoke/bin/activate
python -m pip install --upgrade pip
python -m pip install dist/*.whl
python -m pip check
hir --version
python -m hir --version
hir --help
hir ping --help
hir traceroute --help
hir arp-scan --help
hir report-export --help
```

Validate the sdist in a separate clean environment:

```bash
python -m venv /tmp/hir-sdist-smoke
. /tmp/hir-sdist-smoke/bin/activate
python -m pip install --upgrade pip
python -m pip install dist/*.tar.gz
python -m pip check
hir --version
python -m hir --version
hir --help
hir ping --help
hir traceroute --help
hir arp-scan --help
hir report-export --help
```

Then confirm:

- `CHANGELOG.md` reflects user-visible changes
- support and compatibility docs still match the real behavior
- no merge-conflict markers or unrelated release artifacts are present
- tag/release notes do not promise support beyond the documented matrix

## Deliberately Outside This Baseline

- automated PyPI publishing
- signed artifacts, provenance attestations, or changelog automation
- live network integration tests in CI for `ping`, `traceroute`, or privileged ARP discovery
- Windows support for live diagnostics
- strong guarantees for heuristic OS detection, vendor enrichment, or third-party plugins
