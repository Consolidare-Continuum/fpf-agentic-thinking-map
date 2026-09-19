# Accepted and shipped — adjacency clearance from negative evidence ("Wumpus World logic")

**Status**: Accepted by operator 2026-09-19 ("accepted, produce the code,
dont overstep") and built the same day, exactly to this spec — every field
listed here (`AdjacentlyCleared`, `AdjacencyClearanceRule`,
`biconditional_clear`, `DecisionRule.adjacency_sensitive`,
`ActiveState.confirm_percept_absent`/`has_adjacency_clearance`,
`never_satisfies_authorization`) is real code now, not a sketch. Shipped as
**ADV-17** in `docs/deep/ADVISORIES.md`. This document is kept as the
design record the implementation is traceable back to, per the same
`REJECTED_*.md`/`DESIGN_*.md` convention every other accepted/rejected
proposal in this directory follows — the reasoning stays even once the
"open questions" below are resolved. Where a question below was resolved
during implementation rather than left for a separate verdict, the
resolution is noted inline; nothing was decided silently.
**Requested by**: operator, 2026-09-19, in two turns: "wumpus world is a bit
adjusted for agentic scopes" + "we added a bit of reversed logic," then
"propose it as based on wumpus world logic."
**Author**: Felix (Claude Code), reconstructing intent — see **Interpretation**
below. I could not find an existing spec for this anywhere (`query_brain_fts`,
`query_fpf_catalog`, and a full grep of this repo and the brain repo all came
back empty except one unrelated citation in an archived snapshot), so
everything past this point is my own technical proposal, not a transcription
of something already decided elsewhere. Correct it if the reconstruction is
wrong.

## Interpretation

Two unexplained phrases needed a real technical referent before I'd write
code against them:

- **"Wumpus World"** — the classic knowledge-based-agent environment from
  Russell & Norvig's *AIAMA* (also the one existing citation in this repo's
  history, `archive/.../SOURCES.md` in the brain repo: "the agent perceives
  clues (breeze = adjacent pit, stench = adjacent wumpus) and uses
  propositional logic to deduce which cells are safe before moving").
- **"Reversed logic"** — I'm reading this as Wumpus World's actual load-bearing
  trick, not a vague gesture at `NOT`/`NotProp` (which already exists and is
  already tested — `check_logic_operators`). In Wumpus World the informative
  event is as often the **absence** of a percept as its presence: `¬Breeze(x,y)`
  lets the agent conclude `¬Pit` for *every* neighbor of `(x,y)` in one step,
  via the biconditional `Breeze(x,y) ⟺ ∃ adjacent Pit`. That's a **sound**
  inference from a negative percept — not the same thing as this library's
  existing closed-world defaults (`ADV-01`/`ADV-02`: missing evidence means
  "insufficient," full stop, never "this proves the opposite").
- **"Adjusted for agentic scopes"** — I'm reading this as: don't propose a
  literal grid/pit/gold game. Generalize the *inference pattern* — a declared
  biconditional between one state's evidence and its neighbors' danger — onto
  `SemanticMap`'s actual graph (the same graph `reachability.py` already
  walks), where "cell" is any state, "adjacent" is `TransitionPrimitive.to_state`/
  `from_state` reachability, and "pit/wumpus" is whatever a domain calls
  `RiskAbove`/a denied `GateCheck`/a `guard` verdict.

If any of those three readings is wrong, everything below is proposing the
wrong thing — say so before any of it gets built.

## What the library does today (the gap, if this reading is right)

Every existing evidence-shaped primitive in this package treats **absence**
as strictly weaker than presence, never as its own kind of proof:

- `EvidencePresent`/`EvidenceFresh` — absence means the proposition is
  `False`; there is no companion "provably absent" state.
- `ADV-01` — expired evidence still satisfies `required_evidence`; the core
  explicitly declines to guess whether staleness should be fatal.
- `ADV-02` — `risk_level` doesn't filter `possible_transitions` on its own;
  the core explicitly declines to guess a risk-routing policy.
- `HasMissingEvidence` — a coarse yes/no on whether *anything* is missing,
  with no notion of what a specific absence would positively imply about a
  *different* state.

This is a deliberate, repeatedly-stated design stance (`ADV-01`/`ADV-02`/
`ADV-06`/`ADV-09`'s whole "no oracles, no future seers" position): the core
does not guess what a missing signal means, because that's a domain policy
question. Wumpus World's biconditional inference is a *sound*, *general*,
*domain-agnostic* logical pattern for exactly this class of question — it
doesn't require guessing a domain's policy, because the map author declares
the biconditional explicitly, the same way `ADV-04`'s `exclusive_with` makes
contradiction-checking opt-in and explicit rather than inferred from action
names. That's why I think this stays in scope under this package's own
stated rules rather than being another `ADV-09`-shaped "we can't know your
domain" wall.

## Formal spec

**Domain.** A `SemanticMap`'s declared transitions induce a graph on states
$S$. Adjacency for this proposal is **undirected** — $c_1 \sim c_2 \iff
\exists\, t \in \text{transitions}.\ \{t.\texttt{from\_state},
t.\texttt{to\_state}\} = \{c_1, c_2\}$ — deliberately *not* the directed
relation `shortest_path_distance`/`forward_reachable` already use, because
Wumpus World's own adjacency is symmetric (a pit at $(x,y)$ produces a
breeze at $(x,y{+}1)$ regardless of which direction a transition happens to
be declared). This resolves what was Open Question 1 in the first draft of
this document.

**Danger predicate.** $D(c)$ — true when $c$ is domain-judged dangerous. Not
defined by this package; supplied by whatever the domain already uses
(`RiskAbove`, a denied `GateCheck`, a bespoke `CustomProp`) — same
non-negotiable boundary `RiskAbove` itself already respects.

**Percept.** A distinguished evidence id $p$, observable at a cell
$c^\ast \in S$ in exactly one of three states: *confirmed present*,
*confirmed absent*, or *unconfirmed* (no observation yet — distinct from
"confirmed absent," per the `ADV-03` variable below).

**Declared biconditional** (`AdjacencyClearanceRule`, one per percept,
map-author-declared, never inferred from map shape — `ADV-04` discipline):

$$ \text{Percept}(p, c^\ast) \iff \bigvee_{c \,\sim\, c^\ast} D(c) $$

**The trick.** Observing $\neg\text{Percept}(p, c^\ast)$ as a *confirmed*
negative (not a missing value) licenses:

$$ \neg\text{Percept}(p, c^\ast) \implies \forall\, c \sim c^\ast.\ \neg D(c) $$

— one confirmed negative percept clears an entire neighborhood in one
inference step, which is the actual mechanism Wumpus World teaches and the
actual gap identified above: this package has no primitive today that lets
a confirmed absence positively clear anything.

## Outcomes of the trick

The trick is a **fact-producing `Prop`**, not a **transition** — by itself
it changes nothing about what `step()`/`attempt_transition()` return. It
only reaches an `Outcome` when a map author wires it into a `DecisionRule`
condition or a `guard_expression`-resolved rule — the same opt-in-or-inert
discipline `RiskAbove` already has (`ADV-02`). Checked against the actual
reachable-outcome table in `ARCHITECTURE.md` (v1.9.6, 9 of 11 declared
`OutcomeKind`s live):

| `OutcomeKind` | Reachable via the trick? | How |
|---|---|---|
| `CONTINUE` | Indirectly | A wired rule's `action_if_true` names a transition; that transition's own `guard_expression` resolution fires it — the clearance never fires anything itself. |
| `ABSTAIN` | Indirectly | An unmet clearance (percept unconfirmed, not confirmed absent) just makes the wired condition `False`, same as any other unmet `DecisionRule`. |
| `COLLECT_EVIDENCE` | Yes | The percept id is an ordinary `required_evidence` entry; a gated transition collects it like any other missing evidence until confirmed either way. |
| `CHANGE_FRAME` | No | Adjacency is intra-context by construction — $\text{Adj}(c^\ast)$ only spans one map's own declared transitions. |
| `IDLE` | No | A property of the candidate-action space being empty, not of any one `Prop`'s value. |
| `BRIDGE` | No | Cross-context adjacency is explicitly unproposed (see "Explicitly not proposed here"). |
| `REVISE_PLAN` | Indirectly | If a newly-cleared neighbor flips a `guard_expression`-bound rule's recommendation, `attempt_transition()`'s existing routing-mismatch path already returns this — no new code path. |
| `AWAIT` | Indirectly | "Percept unconfirmed" is exactly a `PendingInput` — model it with the existing primitive, unchanged. |
| `ESCALATE` | Must never be reachable *by weakening it* | The one direction this must never flow: a clearance must never substitute for a denied `AuthorizationReceipt` or an unmet `requires_human_authorization=True` gate. Enforced structurally — see the `ADV-10` variable below. |

No new `OutcomeKind` is proposed. `ASK`/`PUBLISH` stay declared-but-unreachable, unaffected either way.

## One new variable per adjusted advisory

Ten of the sixteen shipped advisories are genuinely touched by introducing
this mechanism — each gets exactly one new variable, no more, closing the
specific interaction and nothing else. The other six (`ADV-09`, `ADV-11`,
`ADV-12`, `ADV-13`, `ADV-14`, `ADV-16`) have no structural interaction with
a negative-evidence adjacency inference and get none — listed at the end so
the omission reads as checked, not missed.

| Advisory | Interaction | New variable | Closes it by |
|---|---|---|---|
| `ADV-01` (staleness WARN not BLOCK) | A confirmed-absent percept can itself go stale; a clearance built on a stale percept is exactly `ADV-01`'s own gap, one level up. | `danger_percept_evidence_id: str` on `AdjacentlyCleared` (**required**, not optional) | Forces every clearance to cite a real `EvidencePrimitive`, so it inherits `ADV-01`'s existing TTL/`WARN` machinery for free — no second staleness system. |
| `ADV-02` (`risk_level` doesn't filter transitions) | Clearance must not auto-filter `possible_transitions` either, by the same non-guessing default. | `adjacency_sensitive: bool = False` on `DecisionRule` | Mirrors the existing `risk_sensitive: bool` field exactly — a rule only sees `AdjacentlyCleared` facts if it opts in. |
| `ADV-03` (`active_context_id` self-asserted) | "Confirmed absent" is itself a claim with no required provenance — the same self-assertion gap, applied to a percept instead of a context. | `confirmed_by_action: str \| None` on the percept record | Names which concrete action produced the observation, so a harness that cares can verify it instead of accepting an ambient claim. |
| `ADV-04` (contradiction detection opt-in) | A clearance can contradict an independent, directly-asserted danger fact about the same cell. | `contradicted_by: list[str] = []` on `AdjacencyClearanceRule` | Feeds `LogicLayer.consistency_check()` exactly the way `exclusive_with` already does for actions — opt-in, explicit, not inferred. |
| `ADV-05` (independent binary `GateCheck`s don't aggregate) | Several neighbor clearances jointly satisfying one partial-completeness requirement hit the identical aggregation gap. | `clearance_group_id: str \| None = None` on `AdjacencyClearanceRule` | Matches `ADV-05`'s own prescribed fix verbatim: "group evidence that forms one partial-completeness check into one `GateCheck`." |
| `ADV-06` (`PASSIVE` agency not enforced) | A self-declared biconditional is a self-certification: the same agent that benefits from a clearance could, in principle, be the one who wrote the rule granting it. | `declared_by_role_id: str \| None = None` on `AdjacencyClearanceRule` | Lets an opt-in guard refuse to honor a clearance when the currently-acting role matches the declaring role — conflict-of-interest check, not a default restriction. |
| `ADV-07` (`RiskAbove` case-sensitive silent default) | A typo'd state id in the declared neighborhood silently drops that neighbor from the inference instead of erroring. | `strict_state_ids: bool = False` on `biconditional_clear()` | Opt-in loud failure on an unknown state id; default stays silent-skip (fail-safe: under-clears, never over-clears) unless the caller asks for strict mode. |
| `ADV-08` (no persistence surface) | Derived clearances are new cached state with exactly the same reconstruction hazard the stagnation counters already have. | `_adjacency_clearances: dict[str, int]` (`init=False`) on `ActiveState` | Same shape as `_state_visits`/`_evidence_added_at` — inherits `ADV-08`'s exact warning verbatim; a harness that hand-rolls persistence must restore it explicitly. |
| `ADV-10` (`requires_human_authorization` defaults `False`) | The one direction that must never happen: a clearance quietly substituting for a missing human authorization on a destructive transition. | `never_satisfies_authorization: ClassVar[bool] = True` on the clearance evidence type | A structural, non-instance, non-overridable marker `validate_map()` can check to refuse a clearance id ever appearing in a `requires_human_authorization=True` transition's `required_evidence`. |
| `ADV-15` (failed-run XOR terminal, distance ≤ bound) | An adjacency-cleared neighbor of the failure locus could be a valid, closer, safe landing spot than the declared `end_compile_revert` target. | `accepts_cleared_targets: bool = False` on the ADV-15 check configuration | When `True`, `distance <= bound` may be satisfied by the nearest cleared state, not only the literal declared revert target — opt-in, defaults to today's exact behavior. |

**Not adjusted, checked and excluded:** `ADV-09` (compliance mode is a
generic witness over *any* move, not percept-specific — nothing here
changes what it witnesses); `ADV-11` (`safe_alternatives` soundness is
about declared transition alternatives, orthogonal to a Prop-level
inference); `ADV-12`/`ADV-13`/`ADV-14` (legacy F/G, work attribution, `MAY`
semantics — none touch evidence or adjacency); `ADV-16` (upstream `ailev/FPF`
intake — this proposal isn't an upstream commit, so the scope gate doesn't
apply to it).

## What I'd propose shipping (opt-in, additive)

### 1. `fpf_thinking_map/logic.py` — one new `Prop`, one new declaration object

```python
@dataclass
class AdjacencyClearanceRule:
    """Map-author-declared biconditional: Percept(danger_percept_evidence_id)
    <=> OR(D(c) for c in Adj(cell)). Never inferred from map shape (ADV-04).
    """
    danger_percept_evidence_id: str
    contradicted_by: list[str] = field(default_factory=list)       # ADV-04
    clearance_group_id: str | None = None                          # ADV-05
    declared_by_role_id: str | None = None                         # ADV-06


@dataclass
class AdjacentlyCleared(Prop):
    """Wumpus-World-style negative-evidence inference: True when the named
    percept is POSITIVELY confirmed absent (not merely unsupplied) at the
    named cell, per a registered AdjacencyClearanceRule. No registration
    means this always evaluates False -- silent guessing is exactly what
    this must not do (ADV-01/02).
    """
    cell_state: str
    danger_percept_evidence_id: str                                # ADV-01

    def evaluate(self, state: ActiveState) -> bool: ...
```

`DecisionRule` gains one field: `adjacency_sensitive: bool = False` (`ADV-02`).

### 2. `fpf_thinking_map/reachability.py` — one new pure function

```python
def biconditional_clear(
    transitions: Iterable[TransitionPrimitive],
    percept_state: str,
    percept_absent: bool,
    *,
    strict_state_ids: bool = False,                                # ADV-07
) -> set[str]:
    """Given a declared percept is absent at percept_state, return every
    state adjacent (undirected -- see Formal spec) that the biconditional
    therefore proves danger-free.

    Returns the empty set when percept_absent is False -- this function
    computes the graph-membership half of the inference only. It does not
    decide what "danger-free" should be allowed to unlock; same split as
    shortest_path_distance vs. a guard's distance<=bound policy (ADV-15).
    """
```

### 3. `fpf_thinking_map/state.py` — one new private field

```python
_adjacency_clearances: dict[str, int] = field(                    # ADV-08
    default_factory=dict, init=False, repr=False,
)
```

Same shape as `shortest_path_distance` (`ADV-15`'s own precedent from this
week): small, pure, declared-graph functions paired with an opt-in `Prop`
a map author's own `DecisionRule`/guard decides what to *do* with. Nothing
here auto-unlocks anything.

### 3. Draft advisory — candidate `ADV-17` (not added to `ADVISORIES.md` yet)

> **ADV-17 — Adjacency clearance is sound only for a correctly-declared
> biconditional, not for "no evidence yet."**
> **What**: `AdjacentlyCleared`/`biconditional_clear()` only produce a valid
> negative-inference result when the map author's biconditional is actually
> true of the domain (danger at a neighbor really would, always, cause the
> percept at the named cell). A caller that registers a biconditional which
> doesn't actually hold in their domain gets a *confidently wrong* clearance
> — worse than `ADV-01`'s merely-stale evidence, because nothing about a
> false "cleared" reads as uncertain. This is the sharpest advisory in the
> proposal, structurally: Wumpus World's own textbook trick only works
> because the game's designers guaranteed the biconditional; this package
> cannot verify a domain's physics/security model actually satisfies one.
> **How to close the gap**: never auto-declare a biconditional from
> `HasMissingEvidence`/absence-of-a-key alone. Require an explicit,
> reviewed `AdjacencyClearanceRule` per percept, the same discipline
> `ADV-04`'s `exclusive_with` and `ADV-10`'s `requires_human_authorization`
> already ask of a map author for a comparably sharp claim.

Writing the advisory *before* the code, not after, matches how every ADV in
this package's history was produced except the ones filed the same day as
their fix (`ADV-01`..`ADV-14` all predate or ship with their guard). Ships
with the primitive if this is accepted, not as a later patch.

## Versioning — arguing against "v2.0"

I don't think this is a breaking change, and I'd push back on releasing it
as one. Every one of `AdjacentlyCleared`, `biconditional_clear()`, and the
`ADV-17` detector is additive and opt-in — a caller who never registers an
`AdjacencyClearanceRule` sees zero behavioral change, same as `MoveIntent`
(v1.9.0), `PendingInput`/`AWAIT` (v1.8.0), and this week's `ADV-15`
(v1.9.6). Every one of those was **additive**, none of them was a major
version. `CHANGELOG.md`'s own `[Unreleased]`/`Planned` note already reads
"1.9.6+ stays open for whatever's actually ready next" — I'd propose this
(if accepted) as the next minor along that same line, not a 2.0. A real
2.0 would mean something in this list is true, and I don't think any of
them are: a primitive gets removed, an existing `Outcome`/`OutcomeKind`
changes shape for existing callers, or a default behavior changes for a
caller who adopts nothing new. If you specifically want a 2.0 for
non-technical reasons (marketing a bigger release, a version-number
signal), say so and I'll drop this section — but I'm not going to silently
agree that this is architecturally a breaking change when I don't think it
is.

## Explicitly not proposed here

- **Literal grid/spatial primitives** (`Cell`, `Pit`, `Wumpus`, `Gold`) —
  the "adjusted for agentic scopes" reading above means generalizing the
  *inference pattern* onto the existing `SemanticMap` graph, not adding
  game-world vocabulary this package has no use for.
- **Automatic biconditional inference** (the core guessing, from a map's
  shape alone, which evidence IDs biconditionally cover which neighbors) —
  same reasoning as `ADV-04` declining to infer contradiction from action
  names. The map author declares it, or it doesn't fire.
- **Any change to what "cleared" is allowed to unlock** — that stays a
  guard/`DecisionRule` decision on the domain side, per every existing
  `ADV-0x` in this family.

## Open questions — resolved during implementation

1. ~~Is "adjacent" the right relation?~~ Resolved in **Formal spec** above:
   undirected, deliberately not `shortest_path_distance`'s directed BFS.
2. ~~Where does `AdjacencyClearanceRule` live?~~ Resolved: registered on
   `SemanticMap` (`register_adjacency_clearance_rule`, its own registry,
   same pattern as `register_gate`/`register_commitment`) — keyed by
   `danger_percept_evidence_id`, one rule per percept. The dataclass
   itself lives in `primitives.py`, not `logic.py` as first sketched above
   — `primitives.py` has no `ActiveState` dependency and this class didn't
   need one either; only the `Prop` that reads it (`AdjacentlyCleared`)
   belongs in `logic.py`. Purely a which-file decision, invisible to any
   caller.
3. ~~`ClassVar` alone or real enforcement?~~ Resolved: both.
   `never_satisfies_authorization: ClassVar[bool] = True` on
   `AdjacencyClearanceRule`, **and** `ThinkingMapTraversal.validation_errors()`
   gained a real check that scans every `requires_human_authorization=True`
   transition's `required_evidence`/`readiness_refs` for a registered
   clearance id and fails closed on `validate_map()` if found. Went with
   the stated leaning toward actual enforcement.
4. ~~Worked example in `examples.py`?~~ Resolved: no. Followed the actual
   `ADV-15` precedent (not the speculative "or" in the original question)
   — coverage lives in `fpf_thinking_map/verify.py`
   (`check_biconditional_clear`, `check_adjacency_clearance_trick`,
   39/39), not as an 11th scenario in `examples.py`'s public demo list.

One implementation-time refinement beyond the four questions above:
`ActiveState._adjacency_clearances` shipped as `dict[str, dict[str, int]]`
(percept id → {cell: step cleared}), not the flatter `dict[str, int]` this
document's per-advisory table first named. A flat cell → step map couldn't
tell two different percepts clearing the same cell apart — exactly the
kind of unverified-provenance bug `ADV-03`'s own variable exists to avoid,
one layer up. Still one field, still `ADV-08`'s exact persistence-hazard
shape; the value type just needed to be precise once actually implemented.

## Regression guarantee

Same guarantee every prior addition in this package states: a caller who
never constructs `AdjacentlyCleared` or registers an
`AdjacencyClearanceRule` sees zero behavioral change. Nothing here is
implemented yet — this is the proposal, not the build.
