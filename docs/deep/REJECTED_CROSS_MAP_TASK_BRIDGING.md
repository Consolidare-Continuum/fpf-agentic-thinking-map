# Rejected: Cross-Map Composition and Cross-Task State Bridging

**Status**: Rejected — will not be added to this package.
**Date**: 2026-07-24
**Decision by**: igareosh (prichindel.com)
**Investigated at**: v1.9.2

---

## What was proposed

A single agent, not a multi-agent system, can end up driving several map-backed integrations at once during one run — one MCP face for move legality, another for verification/advisories, another for a domain-specific traversal, and so on. The question raised: should the library itself compose two or more of those maps into one merged view for a given step, so the model reasoning over their combined output doesn't get lost or produce a contradiction? And separately: should the library track a task identifier, so a finding the agent already established on one call carries forward automatically to the next task instead of being re-derived?

Both are reasonable things to want. Neither belongs in this package.

## Why it is rejected

**Composition.** Every entry point in this library (`attempt_transition`, `thinking_map_step`, the MCP-facing calls built on top) answers one question against one map: is this move legal from this state, and what does it cost/require. It has no notion of a second map existing at the same time, and it should not grow one. Merging two independently-scoped maps into a single combined view requires join semantics — whose vocabulary wins on conflict, how a legal move in map A interacts with a pending obligation in map B — that this package has no way to define generically, because it depends entirely on what the two maps mean to the caller. That decision belongs to whoever is holding both outputs, not to either map.

**Cross-task memory.** The package is, by design, blind to "task" as a concept. A call answers a question about the state it's given; it does not remember that a previous call under a different context already answered a related question, and it should not start doing so. The one piece of state that survives across calls today — `pending_authorizations`, from the HITL/Ignition Lock work — exists narrowly to close a TOCTOU gap in authorization consumption (see `IGNITION_LOCK_WIND_TUNNEL.md`), not as a general precedent for remembering findings. Widening it into a general evidence cache would take on an open-ended state-management problem (what expires, what's still valid, what happens on conflicting re-entry) this package was never built to own, for a benefit the calling agent can already get for free by writing its own finding down once and referencing it — no new primitive required.

### Same shape as prior rejections

Both halves are the same pattern already on record: solving a coordination problem one layer up from where this package operates. `REJECTED_F17_UNIFIED_TERM_SHEET.md` rejected ecosystem-scale term coordination inside a single terminal package for the same reason — the problem exists at a scope this package doesn't reach, and pulling it in buys process weight without catching a failure mode the package has actually hit. Here, the caller already has cheap tools to solve both problems on its own side: tag each piece of reasoning with which map produced it, resolve one map's step before starting the next rather than interleaving, and persist a finding once in whatever the caller already uses to track work across tasks. That costs the caller a labeling convention. It would have cost this package a stateful, application-aware join engine.

## What would change this

Not "it would be convenient" — that's true of most cross-cutting features. The trigger would be a demonstrated, recurring failure mode where caller-side tagging and single-write persistence provably cannot prevent contradiction or duplicated work, across more than one integration, in a way specific to how *this* package's maps are shaped (as opposed to a generic multi-source-reasoning problem any agent framework has). Absent that, this stays a caller-side concern.

---

prichindel.com | 2026-07-24 | v1.9.2
