# Packaging and Releases

## Packaging approach

HIR now uses `pyproject.toml` as the single packaging source of truth.

- Metadata is defined with PEP 621 in `pyproject.toml`.
- The public version is sourced from `hir.__version__` so runtime reporting and distribution metadata stay aligned.
- `setuptools.build_meta` remains the build backend.
- The repository keeps the existing `src/` layout.
- Runtime package data is declared explicitly for the bundled HTML templates used by `hir report-export`.
- `MANIFEST.in` is limited to source-distribution contents and excludes local/generated directories.

## Local build

Create a clean environment with the build extra and build both artifacts:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[build]"
python3 -m build
```

This produces:

- `dist/hir-<version>.tar.gz`
- `dist/hir-<version>-py3-none-any.whl`

## Local artifact validation

Validate metadata and install both artifact types in clean environments:

```bash
python3 -m twine check dist/*
python3 -m venv /tmp/hir-wheel-smoke
. /tmp/hir-wheel-smoke/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install dist/*.whl
python3 -m pip check
hir --version
python3 -m hir --version
hir --help
hir ping --help
hir traceroute --help
hir arp-scan --help
hir report-export --help
mkdir -p /tmp/hir-wheel-report
python3 - <<'PY'
import json
from pathlib import Path

report_path = Path("/tmp/hir-wheel-report/traceroute.json")
report_path.write_text(
    json.dumps({"host": "example.com", "hops": [[1, "192.168.1.1", 1.23]]}),
    encoding="utf-8",
)
PY
hir report-export /tmp/hir-wheel-report/traceroute.json --output-dir /tmp/hir-wheel-report/html
python3 -m venv /tmp/hir-sdist-smoke
. /tmp/hir-sdist-smoke/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install dist/*.tar.gz
python3 -m pip check
hir --version
python3 -m hir --version
hir --help
hir ping --help
hir traceroute --help
hir arp-scan --help
hir report-export --help
```

Treat [docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md) as the final release checklist before tagging.

## GitHub workflows

### Quality workflow

`.github/workflows/quality.yml` runs on pushes and pull requests. It:

- runs Ruff and scoped mypy checks on the `src/hir` codebase
- runs the pytest suite on Ubuntu and macOS across Python 3.10, 3.11, and 3.12
- produces coverage output and uploads the coverage artifacts from the canonical Ubuntu 3.12 job
- builds the sdist and wheel, runs `twine check`, installs the wheel in a clean virtual environment, and runs CLI/report-export smoke checks
- repeats the install-and-smoke path from the source distribution in a separate clean virtual environment

### Release workflow

`.github/workflows/release.yml` runs on tags that match `v*`. It:

- builds the sdist and wheel
- runs `twine check`
- smoke-tests the wheel and sdist before publication
- creates or updates a GitHub Release and attaches the built artifacts

The release workflow does not assume PyPI credentials.

## Manual platform setup still required

### GitHub

To let the release workflow create GitHub Releases with the default `GITHUB_TOKEN`, repository Actions permissions must allow write access to contents.

### PyPI

PyPI publishing is intentionally not automated yet. The safe next step is trusted publishing, not repository secrets.

Manual setup still required:

1. Create or claim the `hir` project on PyPI.
2. Configure a trusted publisher in PyPI for this repository and the release workflow.
3. Add a publish step or dedicated workflow using `id-token: write` and `pypa/gh-action-pypi-publish@release/v1` only after the PyPI-side trust relationship exists.

## Intentionally deferred

The following items remain deliberately deferred:

- deep CLI redesign or architecture refactors
- wider CI matrix expansion
- bundling a real OUI vendor database that is not currently present in the repository
- PyPI publication activation before trusted publishing is configured
- signed artifacts, provenance, or other higher-assurance release automation
