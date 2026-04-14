# HIR Roadmap

This roadmap describes the intended sequence for professionalizing HIR. The project is currently an early-stage Python CLI with a deliberately narrow public scope centered on `ping`, `traceroute`, `arp-scan`, and `report-export`.

The ordering matters. Packaging, testing, architecture, and consistency come before broad feature expansion.

## Direction

- Keep HIR Python-first until the current CLI surface is reliable, testable, and consistently documented.
- Treat documentation accuracy, installation correctness, and repository hygiene as foundation work rather than optional polish.
- Distinguish validated diagnostics from heuristic enrichment in both code and public messaging.
- Expand scope only when the existing workflow is stable on a clean environment.

## Phase 1: Foundation Work

Goal: establish a consistent and professional public identity for the repository.

Focus areas:

- make `README.md` the public source of truth for scope, limits, and usage
- align `ROADMAP.md`, `CONTRIBUTING.md`, and `SECURITY.md` with the real project state
- clean repository hygiene so local environments and generated artifacts are not tracked
- align package metadata and repository-facing language with the validated Python CLI
- remove or stop implying unsupported public promises

## Phase 2: Reliability Work

Goal: make the validated workflow dependable on a fresh setup.

Focus areas:

- verify that editable installation and CLI entry points work cleanly on a new Linux environment
- strengthen automated tests around the validated commands and export paths
- ensure packaged templates and supporting data are included and behave predictably
- document platform assumptions, privilege requirements, and failure modes clearly
- separate validated output from optional or heuristic enrichment more cleanly

Exit criteria:

- a clean install can run `hir --help` and the documented command help paths
- the automated test suite covers the validated surface with confidence
- documentation and CI reflect the same supported workflow

## Phase 3: UX Work

Goal: improve operator experience without widening scope prematurely.

Focus areas:

- make public CLI language and documentation consistently professional and clear
- improve error handling, help text, and exit behavior for common failure cases
- tighten output naming, report ergonomics, and validation examples
- reduce ambiguity around experimental fields and unsupported workflows

Exit criteria:

- a new user can install HIR, run the validated commands, and understand the limits without reading the source

## Phase 4: Network Feature Expansion

Goal: expand capabilities cautiously after the existing baseline is stable.

Focus areas:

- add new diagnostics or report types only when they fit the conservative CLI model
- improve structured output and report coverage incrementally
- introduce additional network discovery features only with clear validation boundaries

Guardrails:

- no feature expansion that outpaces packaging, tests, or documentation
- every new public command should define prerequisites, privilege requirements, and supported outputs

## Phase 5: Plugin and Rust Work

Goal: evaluate extensibility and performance work after the Python core is mature enough to justify it.

Focus areas:

- define whether a plugin model is actually needed and what stability guarantees it would require
- measure real performance bottlenecks before proposing Rust acceleration
- treat Rust or plugin work as optional, later-stage engineering decisions rather than current branding

Guardrails:

- do not market plugin or Rust support before design, packaging, and maintenance expectations are clear
- keep the Python CLI as the validated public path until a broader architecture is proven

## Sequence Summary

1. Foundation work
2. Reliability work
3. UX work
4. Network feature expansion
5. Plugin and Rust work

## Contribution Alignment

Contributions should match the current phase priorities. For the present workflow, see [CONTRIBUTING.md](CONTRIBUTING.md).
