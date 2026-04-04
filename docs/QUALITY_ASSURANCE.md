# Quality Assurance

HIR phase 4 adds explicit quality gates around the validated Python CLI workflow. The goal is to make changes safer without expanding the public surface or pretending the project is more mature than it is.

## Quality Gates

- `ruff` enforces baseline linting and import hygiene across `src/` and `tests/`.
- `mypy` type-checks `src/hir` with pragmatic settings and targeted import fallbacks for optional third-party tooling.
- `pytest` remains the main regression suite.
- Coverage is measured with `pytest-cov` against the `hir` package.
- Coverage currently fails below `85%`.
- Build validation uses `python -m build` and `python -m twine check dist/*`.
- Artifact smoke validation installs the wheel into a clean virtual environment and runs:
  - `hir --help`
  - `hir ping --help`
  - `hir traceroute --help`
  - `hir arp-scan --help`
  - `hir report-export --help`
- The packaging smoke path also verifies `hir report-export` from the installed wheel so packaged templates are exercised.

## Test Organization

- `tests/test_ping.py` and `tests/test_traceroute.py` cover subprocess parsing and command failure handling.
- `tests/test_cli_ping.py`, `tests/test_cli_map.py`, and `tests/test_network_facade.py` cover public CLI wiring and the remaining compatibility facade.
- `tests/test_models.py`, `tests/test_errors.py`, `tests/test_arp.py`, `tests/test_vendor.py`, and `tests/test_fingerprint.py` cover the refactored core modules added in phase 3.
- `tests/test_output_console.py`, `tests/test_output_json.py`, `tests/test_output_json_loading.py`, and `tests/test_output_html.py` cover console rendering, JSON/HTML export, report loading, and file generation behavior.
- `tests/test_output_files.py` covers sequential file naming and post-write permission handling.
- Representative report payloads live under `tests/fixtures/reports/`.

## CI Validation

`.github/workflows/quality.yml` is the main validation workflow for pushes and pull requests.

- `quality-gates` runs on Ubuntu with Python 3.12 and executes Ruff, mypy, and pytest with coverage reporting.
- `test-matrix` runs pytest on Ubuntu and macOS across Python 3.10, 3.11, and 3.12.
- `package-smoke` builds the package, checks metadata, installs the wheel into a clean environment, and runs CLI help plus report-export smoke checks.
- `.github/workflows/release.yml` remains tag-driven and focuses on building release artifacts and attaching them to GitHub Releases.

## Local Validation

The recommended local sequence is:

```bash
python -m ruff check src tests
python -m mypy
python -m pytest -q
python -m pytest --cov=hir --cov-report=term-missing --cov-report=xml -q
rm -rf dist/
python -m build
python -m twine check dist/*
hir --help
hir ping --help
hir traceroute --help
hir arp-scan --help
hir report-export --help
```

For a clean wheel-install smoke test, use the sequence documented in [docs/PACKAGING_AND_RELEASES.md](docs/PACKAGING_AND_RELEASES.md).

## Intentionally Deferred

- Live integration tests against real `ping`, `traceroute`, `nmap`, or privileged ARP traffic remain environment-dependent and are not part of CI.
- Mypy is intentionally scoped to `src/hir`; the test suite is not part of the enforced typing target.
- Heuristic OS detection is still best-effort and should not be treated as authoritative fingerprinting.
- Vendor enrichment still depends on optional OUI data that is not bundled in the repository.
- Windows-specific command compatibility is still outside the validated workflow.
