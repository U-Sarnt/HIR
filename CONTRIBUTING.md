# Contributing to HIR

HIR is currently maintained as an early-stage, Python-first CLI. Contributions should strengthen the validated workflow before expanding scope.

## Current Workflow

- The validated public surface today is `ping`, `traceroute`, `arp-scan`, and `report-export`.
- Python is the active implementation path. Rust, plugin, or broader platform work is future-facing unless a change is explicitly scoped and marked experimental.
- Documentation, packaging, tests, and consistency are higher priority than new feature growth.

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

Run the baseline checks before opening a pull request:

```bash
python -m pytest -q
hir --help
hir ping --help
hir traceroute --help
hir arp-scan --help
hir report-export --help
```

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
- In the pull request description, include the motivation, scope, validation performed, and any remaining limitations.
- If a proposal would broaden the validated public scope, discuss it in an issue or design note before implementation.
