# Proposed (not accepted, not built) — adjacency clearance from negative evidence ("Wumpus World logic")

**Status**: Draft proposal only. No verdict recorded, no code written, nothing
scheduled. This document exists so "propose it" has something concrete to
react to — accept, amend, or reject, the same three-way choice every other
`REJECTED_*.md` / `DESIGN_*.md` in this directory went through before landing.
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

## What I'd propose shipping (opt-in, additive)

### 1. `fpf_thinking_map/logic.py` — one new `Prop`

```python
@dataclass
class AdjacentlyCleared(Prop):
    """Wumpus-World-style negative-evidence inference: True when a declared
    danger percept is POSITIVELY absent at every state adjacent to the one
    named, per a biconditional the map author declares (not inferred).

    Requires the caller to have registered an AdjacencyClearanceRule
    (below) naming which percept-evidence-id biconditionally covers which
    neighborhood. Absence of registration means this always evaluates
    False -- silent guessing is exactly what this must not do (ADV-01/02).
    """
    cell_state: str
    danger_percept_evidence_id: str

    def evaluate(self, state: ActiveState) -> bool: ...
```

### 2. `fpf_thinking_map/reachability.py` — one new pure function

```python
def biconditional_clear(
    transitions: Iterable[TransitionPrimitive],
    percept_state: str,
    percept_absent: bool,
) -> set[str]:
    """Given a declared percept is absent at percept_state, return every
    state one hop away (both directions -- adjacency, not directed reachability)
    that the biconditional therefore proves danger-free.

    Returns the empty set when percept_absent is False -- this function
    computes the graph-membership half of the inference only. It does not
    decide what "danger-free" should be allowed to unlock; same split as
    shortest_path_distance vs. a guard's distance<=bound policy (ADV-15).
    """
```

Same shape as `shortest_path_distance` (ADV-15's own precedent from this
week): a small, pure, declared-graph function in `reachability.py`, paired
with an opt-in `Prop` in `logic.py` that a map author's own `DecisionRule`/
guard decides what to *do* with. Neither auto-unlocks anything.

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

## Open questions for whoever gives this a verdict

1. Is "adjacent" the right relation, or should this be scoped to
   `forward_reachable` distance-1 only (directed), matching how
   `shortest_path_distance` already treats the graph as directed?
2. Does a biconditional live on the `ContextPrimitive` (domain-wide) or
   per-`GateCheck` (narrower, more declarations, less risk of a wrong one
   leaking across unrelated parts of a map)?
3. Worth a `run_scenario`-testable worked example in `examples.py` (an 11th
   scenario) before or after a verdict — this package's own convention
   (`ADV-15`'s `check_adv15_distance_and_xor_terminal`) was to build the
   worked example as part of landing the feature, not before proposing it.

## Regression guarantee

Same guarantee every prior addition in this package states: a caller who
never constructs `AdjacentlyCleared` or registers an
`AdjacencyClearanceRule` sees zero behavioral change. Nothing here is
implemented yet — this is the proposal, not the build.
