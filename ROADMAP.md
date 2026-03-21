# HIR — Roadmap & Improvement Plan

This document tracks known issues, technical debt, and the improvement plan to take HIR from its current early-stage state to a production-quality tool.

---

## Current state (as of March 2026)

HIR is a functional early-stage Python CLI for basic network diagnostics. It covers ping, traceroute, ARP scan, MAC vendor lookup, and heuristic OS estimation. The core loop works, but the codebase has significant gaps before it can be considered reliable or extensible.

**Honest score: 55 / 100**

---

## Known problems

### Critical

| # | Problem | Location | Impact |
|---|---------|----------|--------|
| 1 | `src/cli.py` is empty (0 bytes) | `src/cli.py` | Anyone who clones the repo gets a broken install |
| 2 | `src/rust_ext.py` is empty (0 bytes) | `src/rust_ext.py` | Import will succeed but do nothing — silent failure |
| 3 | `Cargo.toml` is empty (0 bytes) | `Cargo.toml` | Implies Rust support that does not exist yet |
| 4 | `Dockerfile` is empty (0 bytes) | `Dockerfile` | Implies containerization that does not exist yet |

### Documentation & consistency

| # | Problem | Impact |
|---|---------|--------|
| 5 | Topics include `rust` and `pyo3` but README states Rust is not in use | Misleads visitors about the actual stack |
| 6 | All 5 recent commits are in Spanish (`fase 1` through `fase 5`) while the rest of the profile uses English | Inconsistent, looks unprofessional on an English-language profile |
| 7 | Commit author email is `thxsanti@gmail.com` instead of `u.sarnt@proton.me` | Does not match public contact info |
| 8 | No badges in README (CI status, Python version, license) | Visitors cannot tell at a glance whether the project is healthy |

### Code quality

| # | Problem | Impact |
|---|---------|--------|
| 9 | No type hints in source files | Harder to maintain and understand |
| 10 | No docstrings in public functions | No inline documentation |
| 11 | OS fingerprinting is heuristic with no stated accuracy | Could mislead users who rely on the output |
| 12 | ARP scan requires root/sudo but this is not communicated clearly in the CLI output | Confusing UX when permissions are missing |
| 13 | `rust_ext/` directory exists but contains no Rust code | Dead weight, confuses the project structure |

---

## Improvement plan

Organised by priority. Each tier builds on the previous one.

---

### Tier 1 — Fix what is broken (this week)

These are blockers. Nothing else matters until these are done.

- [ ] **Fill `src/cli.py`** with the actual CLI entry point using `argparse` or `click`.
- [ ] **Fill `src/rust_ext.py`** with a proper stub or remove it entirely until Rust is actually implemented.
- [ ] **Delete or fill `Cargo.toml`** — if Rust is not planned short-term, delete it. If it is, add the workspace definition.
- [ ] **Delete or fill `Dockerfile`** — a minimal working Dockerfile takes 10 lines. Either write it or remove it.
- [ ] **Fix topics** — remove `rust` and `pyo3`, replace with `networking`, `cli`, `network-diagnostics`, `scapy`.
- [ ] **Add README badges** — at minimum: CI status, Python version, license.

```
git config --global user.email "u.sarnt@proton.me"
```

---

### Tier 2 — Make it installable and testable (next 2 weeks)

- [ ] **Publish a working `pip install`** — verify `pip install -e .` produces a usable CLI command with `hir --help`.
- [ ] **Write real unit tests** — at minimum test ping parsing, traceroute parsing, and ARP result structure. Aim for >60% coverage.
- [ ] **Add CI badge that actually passes** — a green CI badge on the README is worth more than any amount of documentation.
- [ ] **Fix all commit messages going forward** — use conventional commits in English: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`.
- [ ] **Add type hints** to all public functions in `src/hir/`.
- [ ] **Add docstrings** to all public functions.

---

### Tier 3 — Make it useful beyond basic diagnostics (1 month)

This is where HIR stops being a practice project and starts being something others would actually use.

- [ ] **Structured output** — add `--format json` flag so results can be piped to other tools.
- [ ] **Host discovery mode** — scan a CIDR range and return live hosts with MAC, vendor, and estimated OS in a table.
- [ ] **Port scan integration** — lightweight TCP connect scan on common ports (no nmap dependency required).
- [ ] **HTML report improvements** — make the exported report self-contained (inline CSS/JS), with timestamps and scan metadata.
- [ ] **Proper permission handling** — detect when ARP scan is run without root and show a clear, actionable error instead of a traceback.
- [ ] **`--timeout` and `--retries` flags** — currently hardcoded or missing; expose them as CLI options.
- [ ] **OUI database bundled with the package** — do not depend on an external file being present; ship a compressed OUI database as a package resource.

---

### Tier 4 — Production quality (2–3 months)

This tier turns HIR into a tool that a security engineer would reach for on the job.

- [ ] **Rust extension (optional but powerful)** — implement the ping/traceroute parsing in Rust via PyO3 for measurable performance on large scans. This would justify the `rust` topic and `rust_ext/` directory.
- [ ] **Async scan engine** — replace sequential host scanning with `asyncio` for parallel execution. This makes a meaningful difference at /24 and larger.
- [ ] **Plugin architecture** — allow users to register custom scan modules without forking the project.
- [ ] **`--diff` mode** — compare two scan results and highlight new/missing hosts or changed ports. Useful for network monitoring.
- [ ] **Publish to PyPI** — a proper `pip install hir` with versioned releases.
- [ ] **Docker image** — a working `Dockerfile` that produces a container with all dependencies pre-installed, including those that require root (Scapy, raw sockets).
- [ ] **Man page / shell completions** — generated via `click` or `argparse` for a professional CLI experience.

---

### Tier 5 — Stand-out features (ongoing)

Features that would make HIR genuinely notable in the Python networking tool space.

- [ ] **CVE correlation** — cross-reference discovered services/versions against a local NVD snapshot.
- [ ] **Timeline view** — store scan history locally (SQLite) and show how the network has changed over time.
- [ ] **Web UI mode** — `hir serve` starts a local web dashboard showing live scan results and history.
- [ ] **Integration with Aegis-Agent** — HIR discovering a host could trigger an Aegis-Agent scan of that host's exposed configuration endpoints.

---

## Success metrics

How to know HIR has reached each tier:

| Tier | Signal |
|------|--------|
| 1 | `pip install -e . && hir --help` works without errors |
| 2 | CI is green, coverage >60%, `pip install hir` installs a working tool |
| 3 | A person unfamiliar with the project can run a subnet scan and get structured JSON output in under 5 minutes |
| 4 | The tool is published on PyPI with a versioned release and a working Docker image |
| 5 | HIR appears in search results for Python network diagnostic tools |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All contributions should target an open issue or create one first.
