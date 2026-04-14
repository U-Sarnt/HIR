# Support and Compatibility

## Policy Terms

- Supported: exercised in CI and documented as part of the validated workflow
- Best-effort: may work, but HIR does not make a strong release promise
- Unsupported: outside the validated workflow and may fail without compatibility work

## Python Versions

| Python version | Status | Notes |
| --- | --- | --- |
| 3.10 | Supported | Part of the test matrix |
| 3.11 | Supported | Part of the test matrix |
| 3.12 | Supported | Part of the test matrix and primary release job |
| 3.13+ | Best-effort | Do not treat as supported until added to CI and release validation |
| <3.10 | Unsupported | Outside package requirements |

## Platform Posture

| Platform | Status | Scope |
| --- | --- | --- |
| Linux | Supported | Install, build, CLI help, report export, and validated live diagnostics |
| macOS | Best-effort | Install, tests, CLI help, and report-export paths may work; live diagnostics are not a strong promise |
| Windows | Unsupported for live diagnostics | `ping`, `traceroute`, and `arp-scan` are outside the validated workflow |

HIR should be treated as Linux-first for real network diagnostics. Non-Linux environments are not
marketed as equivalent targets.

## External Dependencies and Privileges

### Required for specific live commands

- `hir ping`: system `ping` binary available in `PATH`
- `hir traceroute`: system `traceroute` binary available in `PATH`
- `hir arp-scan`: raw-socket access through root privileges or equivalent capabilities such as
  `CAP_NET_RAW` or `CAP_NET_ADMIN`

### Required for packaging and report workflows

- Python packaging tooling for local builds (`build`, `twine`) when performing release validation
- bundled Jinja templates for `report-export` are part of the package and are expected to work from
  both wheel and sdist installs

### Best-effort or optional dependencies

- MAC vendor enrichment depends on optional OUI data and is not guaranteed to produce a vendor
  label
- heuristic OS detection may consult `nmap`, SNMP, Scapy, or TTL hints when available, but those
  outputs are not part of the validated diagnostic core

## Public Compatibility Baseline

HIR keeps these contracts stable unless documentation and release notes explicitly say otherwise:

- command names and primary options for `ping`, `traceroute`, `arp-scan`, and `report-export`
- CLI stdout/stderr behavior and exit codes documented in `docs/CLI_OUTPUT_CONTRACTS.md`
- JSON report schema versioning and compatibility rules documented in
  `docs/CLI_OUTPUT_CONTRACTS.md`
- builtin plugin capability registration for the current acquisition, output, and report-loading
  paths

## Versioning and Deprecation Expectations

- HIR uses semantic-style public versions, but still operates in a conservative `0.x` maturity
  stage
- patch releases should focus on fixes, packaging, docs, or low-risk hardening
- minor releases may extend the validated workflow, but should still avoid surprise breakage
- incompatible changes must be called out in `CHANGELOG.md` and in the relevant support/contract
  docs
- deprecations should be announced before removal whenever feasible

## Explicit Support Limits

- Windows live-command compatibility is not supported
- macOS live-command behavior is not promised even though parts of the codebase are tested there
- live diagnostics remain environment-dependent and are not fully integration-tested in CI
- vendor data and OS fingerprinting remain best-effort enrichment, not authoritative facts
- third-party plugins are possible through entry points, but they are not yet treated as a broad,
  stable public ecosystem
