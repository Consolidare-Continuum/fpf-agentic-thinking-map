# Positioning vs ailev/FPF, and a COUNTER: Operational Decision Frames

**Filed**: 2026-08-01
**Triggering upstream commit**: `ailev/FPF` `60caecb` "no U.BoundedContext in FPF from now (A.1.1)" (2026-07-26)
**Disposition**: REJECT the ontology change as something requiring a runtime response (it doesn't — see Semantic delta), **COUNTER** on the missing execution pattern it leaves behind for anyone actually running an agent.

## Position

`ailev/FPF` owns the evolving formal framework. `fpf-thinking-map` owns the executable frontier: what happens when those ideas have to govern one actual agent's next move, deterministically, in running code. This package is an independent compilation for general runtime use — not a bound translation of the spec, not required to track its document structure, and running in languages/runtimes FPF's own semantics were never written to be translatable into.

A wording or ontology change upstream is evidence to evaluate, not an instruction to execute. Nothing here proposes reverting the U.BoundedContext removal, disputing FPF's right to make it, or restoring a U-kind upstream no longer wants published. The removal is correctly motivated — see below. The COUNTER is about what's missing *underneath* it for an executor, not about the ontology decision itself.

## Semantic delta report

| | Pre-2026-07-26 A.1.1 | Post-2026-07-26 A.1.1 | `fpf_thinking_map.ContextPrimitive` (shipped, all versions) |
|---|---|---|---|
| Kind | `U.BoundedContext`, a U-kind | Not a U-kind. `BoundedModelUseStructure` is a `U.Structure` selected only when three relations' joint organization changes a decision | A runtime dataclass — never claimed to be a U-kind in the FPF sense, but did (wrongly, until today's fix) cite A.1.1 as its source |
| Standing state | Implicit container, presumed durable | None — recovered fresh per decision from `ModelApplicabilityRelation`/`ModelUseRelation`/`ModelExpressionCoherenceRelation` | `SemanticMap.contexts` dict + `_ctx_transition_idx`, built once, held for the life of the process |
| Containment/holarchy | Ambiguous in older text | Explicitly forbidden ("no is-a or containment relations") | Never had it in the shape upstream forbids — `parent_context_id` was flagged as wrong-shape (R02) and removed 2026-06-24, a month before the upstream ban existed |
| Crossing | `ContextBridge`-style crossing implied | **"No boundary crossing participates in this identity"** — crossing isn't a primitive anymore | `ContextBridge` + `cross_bridge()` — a first-class crossing occurrence, unchanged, and not going to change: a traversal engine needs an explicit crossing check at the exact moment a candidate action's target scope differs from the active one (`guards.py: _guard_scope_check`) |
| Recovery model | Not specified operationally | Recover the exact relation the current decision needs, per decision, from world-side facts | Pre-compiled index, queried thousands of times over one traversal, never re-derived from scratch per step |

The two are answering different questions. Post-refactor A.1.1 answers "what is true about model applicability/use/coherence, for one decision, told narratively." `ContextPrimitive` answers "which transitions/gates/evidence/roles are candidates *right now*, on the Nth call this process has made, cheaply enough to check on every single one." FPF's new semantics don't cover the second question at all — they weren't trying to.

## Why the removal itself is right, and not what this COUNTER is about

The forces section of the new A.1.1 (`FPF-Spec.md` ~line 1863) names the real failure mode `U.BoundedContext`-as-holon invited: *"Systems, Work, epistemes, and publications are merged into a context-shaped proxy... a shared model does not merge them"* — and separately, universal-context bias (~line 3229): every assignment forced to carry a context slot whether or not it does real work. Both are legitimate ontology hazards for a specification that has to stay coherent across 51k lines used by many authors. Agreed, no dispute.

## The gap: FPF specifies *what's true*, not *what a running process should hold between calls*

**Minimal agent scenario.** An agent is mid-traversal through a domain map with hundreds of transitions across dozens of contexts (a realistic size — see any of the shipped `examples.py` maps scaled up). At step N, it must decide: which transitions are even candidates from the current state, does the intended one have evidence/gate/role authority, and where's the exit. This question gets asked **every single step**, not once per narrative decision the way A.1.1's press-control worked example frames it.

**What FPF's new semantics produce for this scenario.** Recover `ModelApplicabilityRelation`, `ModelUseRelation`, `ModelExpressionCoherenceRelation` fresh, from the full set of world-side facts, each time the question is asked — because there is deliberately no standing structure to consult (crossing "participates in no identity," and a `BoundedModelUseStructure` is selected only when a decision needs the joint pattern, not held for reuse). Applied literally at every step of a long traversal, this is a full relation-recovery pass over the declared map on every move.

**What the Thinking Map produces.** `SemanticMap` calls itself "the compiled FPF thinking map" in its own docstring (`state.py:73-76`) for exactly this reason. `_ctx_transition_idx` (`state.py:89-99`) is built once, keyed `context_id → from_state → transitions`, and `transitions_for()` (`state.py:138-142`) is an O(1) dict lookup against it — not a re-derivation. This was arrived at independently, out of engineering necessity, not as a stance on FPF ontology.

**Complexity, measured, not asserted** (`bench` script below, run against the real installed `fpf_thinking_map==1.9.3`, 50 contexts × 20 transitions = 1000 transitions, 2000 simulated step queries):

```
indexed  (SemanticMap.transitions_for, shipped):  1.83 us/step
naive full-map scan per step (on-demand recovery): 72.34 us/step
ratio: 39.6x
roles_in_context (shipped, ALREADY unindexed):     18.16 us/step  <- live proof the cost is real today, not hypothetical
```

The ratio scales with total map size, not local frame size — a map with 10x more transitions makes the naive path ~10x worse while the indexed path is unaffected. `roles_in_context` (`state.py:135-136`) is the one place the shipped code still does the naive scan, and it already shows measurable cost at this modest scale — it is the control that proves this isn't a hypothetical comparator, it's the shape of the bug we'd get everywhere if we generalized "recover the relation fresh each time."

Reproduction:
```python
from fpf_thinking_map.primitives import ContextPrimitive, TransitionPrimitive
from fpf_thinking_map.state import SemanticMap
import time
sm = SemanticMap()
for c in range(50):
    sm.register_context(ContextPrimitive(context_id=f"ctx_{c}", label=f"ctx_{c}"))
    for t in range(20):
        sm.register_transition(TransitionPrimitive(
            transition_id=f"ctx_{c}_t{t}", label=f"ctx_{c}_t{t}",
            context_id=f"ctx_{c}", from_state="s0", to_state="s1"))
def naive(sm, ctx, st):
    return [t for t in sm.transitions.values() if t.context_id == ctx and t.from_state == st]
t0=time.perf_counter()
for _ in range(2000): sm.transitions_for("ctx_25", "s0")
t_idx=time.perf_counter()-t0
t0=time.perf_counter()
for _ in range(2000): naive(sm, "ctx_25", "s0")
t_naive=time.perf_counter()-t0
print(t_naive/t_idx, "x slower without the index")
```

**Safety/routing consequence.** Without a compiled, bounded frame, `_guard_scope_check` and `_guard_gate_pass` (`guards.py`) either (a) pay the full-map-scan cost on every guard evaluation at real domain-map scale, which is exactly the kind of cost that gets "optimized away" under deadline pressure by future implementers skipping the check and trusting the model not to attempt cross-scope actions — the precise failure mode guards exist to prevent — or (b) silently reintroduce an ad hoc, undeclared, unaudited cache to make it fast again, which is a worse outcome than a declared one: same cost paid, no visibility, no discipline on what it's allowed to assume. A named execution-layer construct that's explicit about being a computational artifact (not a holon, not asserting containment, not a crossing-participant) is safer than either silently-slow or silently-cached.

**Proposed correction / missing FPF pattern.** FPF's post-refactor A.1.1 is complete for deciding *what's true* about one model-use relation, recovered per-decision, narratively. It has no pattern for what a continuously-running process should hold between decisions to make repeated per-step relation-recovery tractable — that's a different layer (execution/compilation), sitting below spec-level ontology and above raw relation facts. We propose naming it explicitly rather than leaving it unaddressed:

**Operational Decision Frame** (`fpf_thinking_map.ContextPrimitive` is our compiled instance of it): a finite, compiled, non-holonic index over already-governed relations (applicability/use/coherence-shaped, or their domain-specific equivalents) — built once, re-validated (never assumed durable across a relation *change*, only across relation *lookups*) whenever the underlying facts change, and explicitly never given identity, containment, or crossing-participant status. Crossing is not a primitive of the frame; it's the frame being rebuilt or swapped against a different relation set, checked explicitly at the point of use (`cross_bridge()`).

This is offered as a candidate missing execution pattern for FPF to consider — for any downstream implementer building a real-time or high-step-count agent on top of FPF ontology, not just this package — not as a request to restore `U.BoundedContext`.

---

Ref: [`FPF_SOURCE_TO_CODE_RELATION_AUDIT.md`](FPF_SOURCE_TO_CODE_RELATION_AUDIT.md) (R01/R02, predates this removal) · [`FPF_AUDIT_RESPONSE.md`](FPF_AUDIT_RESPONSE.md) (R02 already fixed 2026-06-24, independent of upstream's ban) · `SOURCES.md`, `FPF_FLOOR_MAP.md` (provenance corrected 2026-08-01) · brain-repo ledger: `governance/FPF-THINKING-MAP-VS-AILEV-FPF-POSITIONING.md`

SIGNED: Developer (Felix) | Claude Code context | 2026-08-01 | Operational Decision Frame COUNTER, filed against ailev/FPF 60caecb
