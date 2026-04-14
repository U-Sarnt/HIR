# HIR Roadmap

The staged professionalization plan for HIR is complete through phase 7. This document is now an
archive of that sequence rather than an open-ended promise of future expansion.

Future work should be proposed through normal issue, milestone, and release planning instead of by
extending the original phase ladder.

## Completed Phase Sequence

1. Foundation work
   - public identity, repository hygiene, and scope alignment
   - summary: [docs/PHASE1_SUMMARY.md](docs/PHASE1_SUMMARY.md)
2. Packaging and releases
   - packaging baseline, release workflows, and artifact construction
   - summary: [docs/PHASE2_SUMMARY.md](docs/PHASE2_SUMMARY.md)
3. Architecture cleanup
   - internal module split, compatibility facade reduction, and clearer boundaries
   - summary: [docs/PHASE3_SUMMARY.md](docs/PHASE3_SUMMARY.md)
4. Quality and CI
   - linting, typing, regression coverage, and CI quality gates
   - summary: [docs/PHASE4_SUMMARY.md](docs/PHASE4_SUMMARY.md)
5. CLI contracts and output stability
   - stdout/stderr rules, exit codes, and versioned JSON contract
   - summary: [docs/PHASE5_SUMMARY.md](docs/PHASE5_SUMMARY.md)
6. Extensibility foundation
   - plugin contracts, builtin capability registry, and controlled discovery model
   - summary: [docs/PHASE6_SUMMARY.md](docs/PHASE6_SUMMARY.md)
7. Release readiness and hardening
   - support posture, final packaging validation, versioning discipline, and roadmap closure
   - summary: [docs/PHASE7_SUMMARY.md](docs/PHASE7_SUMMARY.md)

## Post-Phase-7 Baseline

The project should continue with these constraints unless a future release explicitly changes them:

- keep HIR Python-first and conservative
- treat Linux as the validated environment for live diagnostics
- preserve the stabilized CLI contract unless a change is intentional and documented
- prefer packaging, compatibility, and operational clarity over broad feature growth
- document support limits explicitly instead of implying broader guarantees

## Future Work After the Phased Plan

Possible future work is not banned, but it is intentionally outside the closed phase plan:

- new diagnostics that fit the conservative CLI model
- broader release engineering such as signed artifacts or trusted publishing
- deeper plugin commitments only after explicit compatibility decisions
- broader platform support only after real validation, documentation, and maintenance commitment

No future work should be marketed as part of the original professionalization roadmap by default.
