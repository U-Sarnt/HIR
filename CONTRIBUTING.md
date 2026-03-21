# Contributing to HIR

Thank you for your interest in contributing!

## Getting started

1. Fork the repository and create a branch from `master`.
2. Set up the development environment:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

3. Make your changes.
4. Run the test suite before submitting:

```bash
python -m pytest -q
cargo test
```

5. Open a pull request describing what you changed and why.

## Code style

- Python: follow PEP 8.
- Rust: run `cargo fmt` and `cargo clippy` before committing.

## Reporting bugs

Open a GitHub issue with:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Python and Rust toolchain versions

## Feature requests

Open a GitHub issue describing the feature and the use case it solves.
