# HIR

HIR is an early-stage Python CLI for conservative network diagnostics and report export.

## Validated scope

- `hir ping` runs ICMP ping through the system `ping` binary.
- `hir traceroute` runs traceroute through the system `traceroute` binary.
- `hir arp-scan` performs a local ARP scan with Scapy.
- `hir report-export` renders supported JSON reports to HTML through the bundled templates.

## Current limits

- OS fingerprinting is explicitly heuristic. HIR does not claim a validated accuracy rate.
- `ping` and `traceroute` depend on the corresponding system binaries being installed.
- ARP scan requires `root` privileges or equivalent raw-socket capabilities such as `CAP_NET_RAW`.
- The public workflow validated in this repository is Python-only.

## Installation

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

## CLI usage

```bash
hir --help
hir ping 1.1.1.1
hir traceroute example.com --format json
hir arp-scan 192.168.1.0/24 --format html
hir report-export results/json/traceroute_example_com_01.json
```

For JSON and HTML exports, the command prints the generated report path to stdout.

## Recommended validation

```bash
pip install -e .
hir --help
hir ping --help
hir traceroute --help
hir arp-scan --help
hir report-export --help
pytest -q
```

## License

MIT
