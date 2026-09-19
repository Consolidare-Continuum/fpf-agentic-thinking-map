# v2.0.0 build spec — not yet cut

**Status**: Spec only. No version bump committed, no tag, no release.
**Requested by**: operator, 2026-09-19, "recheck and spec a v2.0 build."

## Recheck (done this session, before writing this spec)

- **Local**: `python -m fpf_thinking_map.verify` 39/39, `python -m dev_mcp.test_server` 45/45, working tree clean at `31aa2cb`.
- **Upstream `ailev/FPF`**: `origin/main` HEAD still `8581bcf` (`gh api repos/ailev/FPF/commits/main`) — unchanged since the 2026-09-19 audit already in `FPF_SCOPE_AUDIT_LOG.md`. Nothing new to scope-gate.
- **Live deployment** (`cursor-fpf-test-mcp`, `prichindel:/data/workspaces/fpf-thinking-map`): found stale at `62184ed` (`run_verify` returned 37/37, missing the two `ADV-17` checks) — same drift pattern as the `ADV-15` deploy earlier this session. Fast-forwarded to `31aa2cb` (clean, no local diff to stash this time), re-verified **live through the MCP tool itself**: now 39/39.
- **PyPI**: `v1.9.6`'s publish run is still `completed failure` (`invalid-publisher` — pypi.org's trusted-publisher entry for this project still points at the pre-org-transfer identity, not `Consolidare-Continuum/fpf-agentic-thinking-map`). Unresolved since it was first flagged. This blocks **any** release — 1.9.x or 2.0.0 — until fixed on pypi.org (Project → Publishing), not something fixable from this repo.

## On the "2.0" version number

Stating this once, for the record, since a major-version framing has now been asked for twice: every change since `1.9.5` — `ADV-15`, `ADV-16`, `ADV-17` — is additive and backward-compatible. Nothing removes a primitive, reshapes an existing `Outcome` for an existing caller, or changes default behavior for anyone who adopts none of the new opt-in surface. Under this package's own numbering to date (one minor bump per feature drop, `1.6.0` through `1.9.6`), a strict reading puts this content at `1.10.0`, not `2.0.0`. Specifying `2.0.0` here anyway, since which number to ship under is a release/naming decision that belongs to the operator, not an architectural one this repo's own conventions decide unilaterally. The point of writing this down is narrower than re-arguing it: so nobody reading `CHANGELOG.md`'s `2.0.0` entry later goes looking for a breaking change that was never made.

## What ships in 2.0.0

Everything currently on `main`, unreleased: `ADV-15` (failed-run XOR terminal, `end_compile_revert`, `shortest_path_distance`), `ADV-16` (`ailev/FPF` upstream scope gate, `UPSTREAM_SCOPE_INSPECTION.md`), `ADV-17` (Wumpus World adjacency clearance, `AdjacentlyCleared`/`AdjacencyClearanceRule`/`biconditional_clear`). No new content is specified here — all three are already built, tested, and merged. This document only plans the release packaging around them.

## Build steps (none executed yet)

1. `pyproject.toml`: `version = "2.0.0"`.
2. `CHANGELOG.md`: rename `## [Unreleased]` → `## [2.0.0] - <release date>`. The `ADV-15`/`ADV-16` entry already lives under `[1.9.6]` and stays there unchanged — `2.0.0`'s own entry lists only its delta (`ADV-17`), same as every prior release lists only its own delta, not a cumulative diff.
3. `docs/VERSION_TRACKER.md`: new `## v2.0.0 — <date> — <working name>` entry, three practical benefits per the file's own convention; title line bump to "v1.0.0 through v2.0.0".
4. `ARCHITECTURE.md`: revision stamp bump to `v2.0.0 (<date>)`.
5. **Working name**: proposing **"Positive Control"** — next in the existing FAA-safety sequence (Ignition Lock 1.6, Clearance 1.7, Holding Pattern 1.8, Tail Number 1.9, Ground Stop 1.9.5, Missed Approach 1.9.6) and a literal fit for `ADV-17`'s actual point: in ATC, an aircraft under positive control has continuous, *verified* guidance, never an assumed-safe default — exactly the distinction between a real `AdjacencyClearanceRule` confirmation and guessing from missing evidence. Substitutable if there's a preferred name.
6. Build + verify against the actual artifact, same discipline as `1.9.6`: `python -m build`, install the wheel into a clean venv, `python -m fpf_thinking_map.verify`.
7. Commit the version bump, push to `origin/main`.
8. `gh release create v2.0.0` — triggers `publish.yml`. **Blocked** until the PyPI trusted-publisher config is fixed; otherwise this repeats `v1.9.6`'s exact `invalid-publisher` failure.
9. Sync the prichindel MCP workspace again after the push, same manual step every prior release has needed (`ATM-ADV-074`'s pattern) — not automated by this spec, flagged as a standing gap rather than silently worked around.

## Regression guarantee

Identical to the guarantee each underlying commit already states on its own: a caller who adopts none of `ADV-15`/`ADV-16`/`ADV-17`'s opt-in surface sees zero behavioral change from `1.9.5`. The version number changes; the runtime contract for an unmodified caller does not.

## Explicitly not specified here

- **A real breaking change to justify the major version bump.** None was requested. Inventing one to "earn" the `2.0` label would be exactly the ungrounded move this session already declined to make for the original "v2.0, today" ask.
- **The PyPI trusted-publisher fix.** pypi.org account access, outside this repo's or this session's reach.

---

SIGNED: Felix (Claude Code) | fpf-thinking-map context | 2026-09-19 | v2.0.0 build spec, not yet executed
