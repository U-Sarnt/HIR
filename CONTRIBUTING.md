# Contributing to HIR

## Development setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

## Expected validation before opening a PR

```bash
pytest -q
hir --help
hir ping --help
hir traceroute --help
hir arp-scan --help
hir report-export --help
```

## Scope expectations

- Keep the documented workflow aligned with the validated Python CLI.
- Be explicit when a result is heuristic, especially around OS fingerprinting.
- Do not leave placeholder artifacts that imply unsupported Rust or Docker workflows.

## Reporting issues

Open a GitHub issue with:

- A clear problem statement
- Reproduction steps
- Expected behavior and actual behavior
- Python version and relevant system tool versions such as `ping`, `traceroute`, or `nmap`
