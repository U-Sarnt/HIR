# HIR

HIR is an early-stage Python CLI for basic network diagnostics and report export.

## Current scope

- Ping and traceroute using system binaries.
- Local ARP scan with Scapy.
- MAC vendor lookup when a local OUI database is available.
- Heuristic operating system estimation for hosts discovered during ARP scan.

## Relevant limitations

- Operating system results are heuristic estimates. This project does not currently validate or guarantee an accuracy percentage.
- Some features depend on system tools such as `ping`, `traceroute`, and, for some fingerprint attempts, `nmap`.
- ARP scan requires suitable network privileges such as `root` or equivalent capabilities.
- `Cargo.toml`, `Dockerfile`, and `rust_ext/` are present in the repository, but they are not part of the documented or validated usage path in the current state of the project.

## Requirements

- Python 3.10+

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Recommended validation

```bash
python -m pytest
```

## Status

This project is in early development. The current goal is a maintainable CLI with conservative, observable behavior rather than broad capability claims.

## License

MIT
