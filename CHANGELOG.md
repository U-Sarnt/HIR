# Changelog

All notable changes to HIR's validated public surface, release posture, and compatibility policy
should be recorded here.

The project keeps the changelog intentionally conservative:

- document user-visible CLI, packaging, compatibility, schema, and support changes
- describe incompatible changes explicitly
- note deprecations before removal whenever feasible

## Unreleased

### Added

- release-readiness, support, and phase-7 closure documentation
- `hir --version` and `python -m hir` as stable version/reporting entry paths
- packaging smoke validation for both wheel and sdist artifacts

### Changed

- package metadata now reads the public version from `hir.__version__` so the source package and
  built distribution share a single version source of truth
- release workflows now verify installability, dependency health, CLI help, and report-export
  behavior before a GitHub release is published

### Fixed

- missing `ping` and `traceroute` binaries now fail with clearer operational guidance
- `arp-scan` now fails explicitly on Windows instead of relying on downstream runtime behavior
