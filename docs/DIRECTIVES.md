# Directive status of this repository's decisions

A decision is a **DIRECTIVE** only if it is named, custodied here, scoped, accepted (signed) and backed by
executable evidence. Otherwise it is a **PROPOSAL** (not binding) or a **DESCRIPTION** (records what is).
Basis: brain repo `governance/SIGNED-DIRECTIVE-STANDARD.md` (draft). Counter-examples, which are not evidence:
a README sentence, a changelog line, a version number, the word "lawful".

Evidence run 2026-10-22: `python3 -I -m fpf_thinking_map.verify` → **39/39 checks passed** (version 2.0.1).
Scope of that evidence: the library's own primitives, not any downstream map built on it.

| Decision (see [DECISIONS_REJECTIONS_ADOPTIONS.md](DECISIONS_REJECTIONS_ADOPTIONS.md)) | Status | Evidence (verify.py check) |
|---|---|---|
| A.15.5 Work-Entry Readiness | DIRECTIVE | `slice blockers (HITL)`, `semantic floors (FPF vertical)` |
| Ignition Lock: transitions needing a human do not auto-fire | DIRECTIVE | `requires_human_authorization transition (no model auto-fire)` |
| AuthorizationReceipt (Clearance): scoped, non-replayable, TOCTOU-safe | DIRECTIVE | `authorization receipt (scoped, non-replayable, TOCTOU-safe)` |
| PendingInput / AWAIT distinct from IDLE | DIRECTIVE | `pending input / AWAIT (distinct from IDLE)` |
| MoveIntent (Tail Number) | DIRECTIVE | `move intent / inspect_move (concrete move identity)` |
| Reachability analysis | DIRECTIVE | `reachability`, `shortest_path_distance` |
| Agentic structural guards are opt-in | DIRECTIVE | `agentic structural guards are opt-in` |
| Traversal Checkpoint and Restore | PROPOSAL | accepted, implementation pending; no code, no check |
| All `REJECTED_*.md` | DESCRIPTION | decision records; bind nothing |
| `ADV-*` advisories | DESCRIPTION | integrator-facing known gaps, not guarantees |

## Limits

- A DIRECTIVE here means "the library behaves so, as checked". It does not make a downstream integrator's map compliant.
- Phrases such as "lawful transitions" in README/docs are descriptive vocabulary, not a legal claim and not a certification (cf. Referat 348 §5).
- Acceptance is by signature below; until a role other than the drafter signs, rows stay as classified by the drafter.

SIGNED: Developer (Felix) | Claude Code context | 2026-10-22 | classification of existing decisions vs verify.py 39/39; acceptance pending
