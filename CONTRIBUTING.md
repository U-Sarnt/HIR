# Contributing to HIR

HIR is currently maintained as an early-stage, Python-first CLI. Contributions should strengthen the validated workflow before expanding scope.

## Current Workflow

- The validated public surface today is `ping`, `traceroute`, `arp-scan`, and `report-export`.
- Python is the active implementation path. Rust, plugin, or broader platform work is future-facing unless a change is explicitly scoped and marked experimental.
- Documentation, packaging, tests, and consistency are higher priority than new feature growth.
- Support promises must stay aligned with the documented matrix in `docs/SUPPORT_AND_COMPATIBILITY.md`.

## Local Setup

Prerequisites for live command checks:

- Python 3.10 or newer
- `ping` available in `PATH`
- `traceroute` available in `PATH`
- root privileges or equivalent raw-socket capabilities if you plan to run live ARP scans

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Tests and Validation

Run the standard validation sequence before opening a pull request:

```bash
python -m ruff check src tests
python -m mypy
python -m pytest -q
python -m pytest --cov=hir --cov-report=term-missing --cov-report=xml -q
rm -rf dist/
python -m build
python -m twine check dist/*
hir --version
python -m hir --version
hir --help
hir ping --help
hir traceroute --help
hir arp-scan --help
hir report-export --help
```

For full artifact smoke validation, install both the built wheel and sdist in clean virtual environments and rerun the version/help checks:

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

The complete release checklist lives in [docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md).

If your change affects live diagnostics, validate it on a controlled Linux environment with the required system tools and privileges.

## Coding Expectations

- Keep public documentation aligned with actual CLI behavior.
- Be explicit when behavior is heuristic, experimental, or dependent on external tooling.
- Prefer focused changes that improve clarity, reliability, or packaging over broad feature additions.
- Preserve the project tone: conservative, evidence-oriented, and automation-friendly.
- Do not commit local virtual environments, generated results, or other machine-specific artifacts.

## Commits and Pull Requests

- Use clear English commit messages that describe the change.
- Keep each pull request focused on one problem, decision, or slice of work.
- Update tests or documentation when public behavior, installation steps, or validation guidance changes.
- Update `CHANGELOG.md` when a change affects the public CLI, packaging behavior, support posture, or compatibility expectations.
- In the pull request description, include the motivation, scope, validation performed, and any remaining limitations.
- If a proposal would broaden the validated public scope, discuss it in an issue or design note before implementation.
