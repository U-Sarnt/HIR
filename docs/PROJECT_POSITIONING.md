# HIR Project Positioning

HIR is an early-stage Python CLI for conservative network diagnostics and report export. Its role today is to provide a small, automation-friendly command surface for standard network checks while being explicit about operational limits, privilege requirements, and heuristic output.

## Target Audience

- network engineers and administrators
- operators who prefer shell-first workflows
- teams that need simple structured exports from a narrow diagnostic CLI

## Validated Scope Today

- `ping`
- `traceroute`
- `arp-scan`
- `report-export`

## Non-Goals for the Current Stage

- broad asset inventory or vulnerability scanning
- aggressive or high-speed network enumeration
- a stable plugin ecosystem
- Rust-based performance work as part of the public contract

## Long-Term Ambition

Build a trustworthy, automation-oriented network diagnostics CLI that expands carefully only after packaging, testing, and public consistency are solid.
