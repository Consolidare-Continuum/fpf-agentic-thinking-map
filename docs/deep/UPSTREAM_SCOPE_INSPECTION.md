# Upstream scope inspection (`ailev/FPF` → our scopes)

**Status**: Adopted as true (operator, 2026-09-19) — second thread alongside ADV-15.
**Advisory face**: [`ADV-16`](ADVISORIES.md#adv-16--ailevfpf-commits-must-pass-our-predefined-scopes--else-tombstone).
**Ledger**: brain `governance/FPF-THINKING-MAP-VS-AILEV-FPF-POSITIONING.md` disposition table; package mirror `FPF_THINKING_MAP_VS_AILEV_FPF_POSITIONING.md` / `FPF_SCOPE_AUDIT_LOG.md`.

## Rule (non-negotiable)

Commits (or commit groups) in the **ailev/FPF** source repository are **not** instructions to execute and are **not** silently in scope for `fpf-thinking-map`.

Each material upstream commit **must** be inspected against the **predefined scopes** below (proposed / advised for *our* executable frontier). Exactly one of:

| Verdict | Meaning |
|---------|---------|
| **PASS** | Commit respects our scopes → **follow** it into our scopes via the disposition protocol (`ADOPT` / `ADAPT` / `HOLD` / `COUNTER` as appropriate). Record the ledger row. |
| **FAIL** | Commit does **not** respect the conditions → **TOMBSTONE** it (and/or any advisory that would pretend it is in scope). Do not ship, do not cite as runtime authority, do not leave unclassified forever. |

Silence is not PASS. An unclassified upstream commit is **open**, not accepted.

## Predefined scopes (our package)

A candidate passes **only if** it can be answered yes under every row that applies. These are the scopes we proposed/advised for this carrier — not ailev's full ontology surface.

| ID | Scope condition | Fail signal |
|----|-----------------|-------------|
| **S1** | Changes **one lawful runtime move** — admissibility, routing, waiting/Holding, authorization/Ignition, or evidence reliance | Ontology-only / naming / publication-ecosystem churn with no move effect |
| **S2** | Fits the **executable frontier** — compilable into deterministic `step()` / `slice()` behavior | Requires the model to re-reason the framework, self-admit, or widen the branch space (C.32 / NQD class) |
| **S3** | Keeps the **compiled surface small** — does not force a new self-governing meta-protocol for adding patterns to this package | Would make this repo need its own E.20 / F.17 / F.8-scale self-management |
| **S4** | Has a **scenario or HOLD** — either a minimal agent scenario proves the delta, or disposition is explicit `HOLD` | Silent ADOPT because “upstream said so” |
| **S5** | Provenance stays honest — citations match what upstream still publishes; wrong citations are corrected without pretending runtime must track document structure | Blind rename/hard-cut of live primitives because upstream relitigated a term |

Reference: `SOURCES.md` (“compile only structures that change one lawful runtime move”), audit R56/R57 activation triggers, `WHY_THIS_EXISTS.md`, disposition protocol ADOPT/ADAPT/REJECT/HOLD/COUNTER.

## TOMBSTONE

**TOMBSTONE** is a recorded fate, not a soft ignore.

1. **Upstream commit / group** — ledger row disposition **TOMBSTONE** (or **REJECT** with tombstone marker) + optional `REJECTED_*.md` / scope-audit row. Must not be treated as in our scopes.
2. **Advisory** — if an `ADV-*` (or proposed advisory) **does not respect** these scope conditions — e.g. it would pull ontology-only upstream into the runtime, or claim PASS without inspection — **tombstone that advisory**: mark superseded / not respecting conditions in `ADVISORIES.md` index (or move reasoning under `REJECTED_*`). Do not leave it live as if still authoritative.

TOMBSTONE ≠ “we disagree with ailev.” It means: **this delta does not meet our predefined scope conditions**, so it does not follow into our scopes.

## Inspection checklist (one commit at a time)

Still **one commit (or declared group) at a time** — same discipline as one `step()` at a time.

1. Name the upstream commit hash + one-line subject.
2. Score S1–S5 (PASS/FAIL/N/A with one evidence line each).
3. If any hard FAIL on S1–S5 → **TOMBSTONE** (commit and any advisory that would claim otherwise).
4. If all applicable PASS → file disposition (`ADOPT`/`ADAPT`/`HOLD`/`COUNTER`) and **follow** into our scopes only as that disposition allows.
5. Update the disposition ledger. No silent backlog forever for material commits.

## Relation to ADV-15

ADV-15 is the failed-run XOR terminal (`end_compile_revert`, 1 step, distance ≤). This document is the **upstream intake** thread. Both are true; neither replaces the other.

---

SIGNED: Cursor | fpf-thinking-map context | 2026-09-19 | upstream scope inspection + TOMBSTONE rule
