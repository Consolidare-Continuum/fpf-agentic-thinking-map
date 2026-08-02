# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Narrative version of this arc, if you want the story instead of the
list: [`docs/deep/EXPANDED_PROVENANCE.md`](docs/deep/EXPANDED_PROVENANCE.md).

## [Unreleased]

### Planned

- Traversal checkpoint and restore — `ActiveState.checkpoint()` /
  `ActiveState.from_checkpoint()`, `SemanticMap.fingerprint()`. Design
  finalized, not yet implemented. See
  [`docs/deep/DESIGN_TRAVERSAL_CHECKPOINT.md`](docs/deep/DESIGN_TRAVERSAL_CHECKPOINT.md).

## [1.9.5] - 2026-08-01

### Fixed

- **A.21 gate lattice was not order-correct** ("Ground Stop"): the runtime
  now keeps "not enough basis to say yes" (`ABSTAIN`) separate from "this
  declared check says no" (`BLOCK`). `BLOCK` is a hard denial for the current
  evaluation, not a claim that the decision can never change; a later change
  in declared evidence, state, or policy can produce a different result. The
  important guarantee is that an active `BLOCK` cannot be diluted by another
  check or mistaken for ordinary uncertainty. `GatePrimitive.evaluate()`
  aggregated multiple `GateCheck` results by checking for `ABSTAIN` before
  `DEGRADE`, contradicting its own declared lattice (`abstain ≤ pass ≤
  degrade ≤ block`, where `BLOCK` should dominate). Confirmed by direct
  test: a mixed `[PASS, BLOCK]` result was silently returning `PASS`, and
  `[ABSTAIN, DEGRADE]` was returning `ABSTAIN` instead of `DEGRADE`. Fixed
  by an explicit `GateDecision.lattice_rank` and a proper `max()` join.
  **What integrators will observe**: a default check with missing declared
  evidence returns gate-level `ABSTAIN` (`"insufficient"`) and traversal can
  return `COLLECT_EVIDENCE`. The same missing evidence on a check that opts
  into `failure_decision=GateDecision.BLOCK` returns a denied outcome with
  `cause=gate_block`. A gate built from several checks where one abstains and
  another degrades now aggregates to `DEGRADE` (→ `WARN`, allowed), not
  `ABSTAIN` (→ denial). If every missing independent requirement must stop the
  move, declare `BLOCK` on each such check instead of relying on aggregation.
- **`GateDecision.BLOCK` was unreachable.** No built-in check could ever
  produce it, and the (now-fixed) aggregation above would have silently
  discarded it if one had. `GateCheck.failure_decision: GateDecision | None
  = None` lets an individual check opt into emitting `BLOCK` when its
  evidence is incomplete; every existing check keeps its exact prior
  PASS/DEGRADE/ABSTAIN behavior since the field defaults to unset.
- **`GateBlocked` tested `ABSTAIN`, not `BLOCK`.** Fixed to test the value
  its name promises. A new `GateAbstained` proposition preserves the exact
  old behavior (including returning `True` for a missing gate) for any
  `DecisionRule` that was intentionally built on the old semantics — this
  package's own shipped deploy-scenario rule was migrated to it.
- **`step()`/`attempt_transition()` returned the same `CONTINUE`-shaped
  result for a nonexistent `transition_id` as a valid one.** Now returns an
  explicit `ABSTAIN` with `cause=OutcomeCause.UNKNOWN_TRANSITION`. Only
  affects callers already passing an ID that doesn't resolve — not a state
  any correct caller could have been relying on.
- Corrected an audit record (`docs/deep/FPF_SOURCE_TO_CODE_RELATION_AUDIT.md`,
  R40) that had marked this gate lattice work "resolved" before the
  aggregation fix above existed. Now reads "partial, repaired" with the
  specifics of what was wrong and what changed.

### Added

- `Outcome.cause: OutcomeCause | None` — additive typed reason distinguishing
  `gate_block`, `unknown_transition`, `context_mismatch`, `logic_contradiction`,
  `claim_scope_denial`, and generic guard denial, without changing any
  existing `OutcomeKind` mapping. Existing callers routing on `OutcomeKind`
  alone see no change; callers that want the distinction can inspect `cause`.
- `ThinkingMapTraversal.validate_map()` / `validation_errors()` — opt-in
  preflight that fails closed on a dangling `required_gate_id` or
  `guard_expression` reference. Runtime traversal keeps its existing silent
  no-op on an unresolved reference for full backward compatibility; new
  integrations should call `validate_map()` once after assembly.
- **Opt-in agentic structural primitives** (`fpf_thinking_map.agentic_structure`):
  typed `ClaimScope`/`ContextSlice`/`FormalityLevel`/`ReliabilityPath`
  alongside the existing scalar `FGR` (unchanged, still readable);
  `CallPlanPrimitive`/`BudgetEnvelope`/`CheckpointReturn` for closed tool-call
  planning (`REVISE_PLAN` on an absent/incomplete/mismatched plan);
  `AutonomyBudgetDecl`/`AutonomyLedgerEntry` for a hard autonomy envelope a
  transition opts into via `requires_autonomy_budget_id`.
  **Everything here is opt-in at the map or transition level.** A map that
  declares no `RoleAssignment`, no `AutonomyBudgetDecl`, and no call plan
  behaves identically to 1.9.4 — verified directly against both original
  regressions this line of work introduced and fixed before release (a
  `WorkPrimitive` without `performed_under` on a legacy map, and an
  `AgencyLevel.AUTONOMOUS` role with no budget declared, both confirmed
  `allowed=True` exactly as in 1.9.4).
- `WorkPrimitive.performed_under` + `SemanticMap.validate_work_attribution()`
  (F.6): once a map declares any `RoleAssignment` at all, the
  `planning_not_enactment` guard requires at least one validly-attributed
  work record for a `_done`/`_complete` transition. A map with zero
  `RoleAssignment`s anywhere retains exactly its 1.9.4 behavior.
- `DeonticModality.MAY` documented and treated at runtime as non-binding
  allowance only — not a permission grant, proof of non-prohibition, or
  transition authorization. Those remain separate, explicit relations.
- Three new advisories (`ADV-12`, `ADV-13`, `ADV-14`) covering legacy scalar
  F/G drift, unresolved F.6 attribution, and MAY/permission confusion — see
  `docs/deep/ADVISORIES.md`.

## [1.9.4] - 2026-07-25

### Fixed

- **`TransitionPrimitive.guard_expression` was declared but never
  consulted** — not read by `guards.py`, `traversal.py`, `state.py`, or
  `logic.py`. `ThinkingMapTraversal.attempt_transition()` now treats a
  non-empty `guard_expression` as a `DecisionRule.name` reference in the
  bound `LogicLayer`: the transition only fires when that rule's current
  recommendation (`action_if_true`/`action_if_false`, whichever the
  condition resolves to) matches the transition_id being attempted.
  Closes #10.
  - A routing-policy mismatch returns `REVISE_PLAN` — not `ESCALATE` — with
    the rule's actual recommendation in `Outcome.alternatives`, so an
    agentic caller can retry the correct transition_id in the same turn.
    `REVISE_PLAN` was declared in `OutcomeKind` since the outcome space was
    first drawn up but never previously returned by any code path.
  - No active recommendation (condition false with no `action_if_false`,
    or a `HINT`/`WARN` rule's vacuous-implication suppression): silent
    pass-through, same as not setting `guard_expression` at all.
  - Dangling reference (no `logic_layer` bound, or the named rule doesn't
    exist): silent no-op, matching `required_gate_id`'s existing
    convention for an unresolved reference — backward compatible with
    every existing map.
- `check_route_gated_transition` added to `python -m fpf_thinking_map.verify`
  (28/28).

## [1.9.3] - 2026-07-24

### Added

- **`fpf_thinking_map.reachability`**: discrete reachability analysis over a
  `SemanticMap`'s declared transition graph — `graph_roots()`,
  `forward_reachable()`, `unreachable_transitions()`. Algorithm 10.1/10.3 from
  M. J. Kochenderfer, S. M. Katz, A. L. Corso, and R. J. Moss, *Algorithms for
  Validation* (MIT Press, 2026), ch. 10 — cheap at domain-map scale (tens of
  transitions), and it checks the actual declared graph instead of only the
  paths a hand-written test happened to exercise.
- `check_reachability` added to `python -m fpf_thinking_map.verify` (27/27).

### Fixed (by the check catching it, not by changing runtime behavior)

- A downstream domain map (outside this package) gave a
  `requires_human_authorization` transition its own dedicated `from_state`,
  distinct from its non-destructive twin's. Read cold, that `from_state`
  looked unreachable — nothing else in the map produced it. The state was
  actually an intentional external entry point (callers arrive there after
  work upstream of the map), not a defect — but nothing recorded that on
  purpose, so a plausible-looking fix (merge it onto the shared `from_state`
  its safe twin used) broke four behavior tests: `ThinkingMapTraversal.step()`
  called without an explicit `transition_id` aggregates `missing_evidence`
  across every transition sharing a `from_state`, not just the one the caller
  meant. Runtime behavior of this package is unchanged by this release —
  `reachability.unreachable_transitions()` requires `entry_states` as an
  explicit argument precisely so an intentional entry point is a one-line,
  reviewable statement instead of tribal knowledge someone has to
  rediscover the hard way, as happened here. Worked example, both directions,
  against this package's own `build_destructive_action_map()`: see
  `check_reachability` in `fpf_thinking_map/verify.py`.

## [1.9.2] - 2026-07-23

### Changed

- Rebuilt the PyPI long description from the current public README, including
  the polished library narrative, seven status badges, important project
  links, and the test-backed runtime visual.
- Converted README assets and repository references to absolute URLs so the
  same document works correctly on both GitHub and PyPI.
- Refreshed package summary, keywords, and project links around
  `AuthorizationReceipt`, `PendingInput`/`AWAIT`, and `MoveIntent`.

This is a documentation and package-metadata release. Runtime behavior is
unchanged from v1.9.1; all 26 deterministic checks still pass.

## [1.9.1] - 2026-07-23

### Fixed

- **`AuthorizationReceipt` expiry**: `expires_at_step`
  was checked against `ActiveState.step_count`, which only advances on
  `step()` — never on `attempt_transition()`/`transition_to()` firing. A
  caller whose workflow only calls `attempt_transition()` got no
  time-based expiry at all: issue two receipts against the same state,
  fire one, fire an unrelated transition back to a fingerprint-identical
  state purely through fires (zero `step()` calls anywhere), and the
  second, never-consumed receipt would still validate. Found via
  adversarial testing against the live engine, not design review.
  Fixed with `ActiveState._authorization_clock`, a counter dedicated to
  receipt freshness that ticks on both `step()` and every successful
  fire — deliberately not merged into `step_count`, which stays scoped to
  evidence TTL decay so this fix doesn't also make evidence go stale
  faster as a side effect.

## [1.9.0] - 2026-07-23

### Added

- **`MoveIntent` / `inspect_move()`** ("Tail Number"): `TransitionPrimitive`
  names a reusable move *type* ("publish"); `MoveIntent` now names one
  concrete proposed move (`move_id`, `transition_id`, `parameters`,
  `requested_by`, `binding_revision`, `parent_move_id`), distinct from
  it — the type/instance conflation `WorkPrimitive`'s own docstring
  already warns against elsewhere in this package.
  `ThinkingMapTraversal.inspect_move(state, intent)` evaluates one
  without firing anything, a thin wrapper over the no-mutation `step()`
  path that already existed. `MoveTrace.move_id`/`parent_move_id` are
  stamped on a successful fire.
- Found during implementation, not in the original design: an intent
  naming a transition other than the one that actually fired is not
  stamped into `trace` (would corrupt lineage with an unrelated move's
  identity) — and `attempt_transition()` surfaces this as a `warnings`
  entry rather than absorbing it silently.
- Deliberately not shipped: `MoveIntent.parameters` does not reset the
  stagnation visit-key. Asserted directly in `check_move_intent`, not
  left as an accident of omission.

See [`docs/deep/EXPANDED_MOVE_INTENT.md`](docs/deep/EXPANDED_MOVE_INTENT.md).

## [1.8.0] - 2026-07-23

### Added

- **`PendingInput` / `OutcomeKind.AWAIT`** ("Holding Pattern"): `IDLE`
  used to mean two different things — "done, nothing left to do" and
  "nothing to do *right now*, but something outside the map is still
  owed." `PendingInput`/`PendingInputStatus` declare an external
  dependency with `wake_conditions`; `AWAIT` fires when nothing else is
  actionable and one is still unresolved. A candidate action or a bridge
  elsewhere still wins over `AWAIT` — waiting never hides an available
  move. The core never polls, schedules, or resolves the dependency;
  status is host/adapter-owned.
- Same design pattern `ADV-08` already forced for
  `pending_authorizations`, applied a second time to a different kind of
  waiting (an external producer, not a human decision).

See [`docs/deep/EXPANDED_PENDING_INPUT_AWAIT.md`](docs/deep/EXPANDED_PENDING_INPUT_AWAIT.md).

### Rejected (reviewed alongside this release, not shipped)

- Runtime affordance/tool-availability projection into every `slice()` —
  by its own design it never changes `can_fire` or any computed outcome.
  See [`docs/deep/REJECTED_RUNTIME_AFFORDANCE_PROJECTION.md`](docs/deep/REJECTED_RUNTIME_AFFORDANCE_PROJECTION.md).
- Mandatory orientation-revision metadata in every `slice()`/
  `to_llm_prompt_state()` call — same reasoning, same rejection. See
  [`docs/deep/REJECTED_ORIENTATION_VIEW_PROJECTION.md`](docs/deep/REJECTED_ORIENTATION_VIEW_PROJECTION.md).

## [1.7.0] - 2026-07-23

### Added

- **`AuthorizationReceipt`** ("Clearance"): `authorized=True` proved *a*
  human said yes, not that they said yes *to this state* — a TOCTOU gap
  named but explicitly left untested in the Ignition Lock wind-tunnel
  writeup. `AuthorizationReceipt` binds an approval to one `transition_id`
  and a hash of the exact state (context, current_state, evidence) it was
  issued against. `attempt_transition()`/`transition_to()` independently
  re-verify transition identity, state fingerprint, expiry, and prior
  consumption before spending one — rejected outright, with a specific
  reason, on any mismatch. `authorized=True` still works for callers who
  haven't migrated.

See [`docs/deep/IGNITION_LOCK_WIND_TUNNEL.md`](docs/deep/IGNITION_LOCK_WIND_TUNNEL.md#2026-07-23-update)
for how this closes (and doesn't close) that document's own stated gaps.

## [1.6.0] and earlier

See [GitHub Releases](https://github.com/Consolidare-Continuum/fpf-agentic-thinking-map/releases)
and [`docs/deep/ADOPTED_IGNITION_LOCK.md`](docs/deep/ADOPTED_IGNITION_LOCK.md).
