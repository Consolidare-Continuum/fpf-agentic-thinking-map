"""Discrete reachability analysis over a SemanticMap's declared transition graph.

A SemanticMap's transitions form exactly the object M. J. Kochenderfer, S. M.
Katz, A. L. Corso, and R. J. Moss describe in *Algorithms for Validation*
(MIT Press, 2026), ch. 10, "Reachability for Discrete Systems": a directed
graph, one node per state, one edge per transition. Their algorithm 10.1
(build the graph) and 10.3 (backward/forward reachable sets) are cheap at the
scale a hand-authored domain map actually runs at -- tens of transitions, not
thousands -- so there is no excuse for skipping them in favor of hand-picked
test cases that only exercise the paths someone happened to think of.

What this module answers: given the transitions a map declares, is every
from_state either a named entry point or produced by some other transition's
to_state? A from_state that is neither is either (a) the map's intentional
starting point for a bounded context -- the caller sets current_state there
directly, e.g. because real-world work upstream of this map already happened
-- or (b) an orphaned typo nobody meant to leave unreachable. This module
cannot tell those apart on its own, and does not try to: entry_states is a
required argument, not inferred, because a map's real entry points are a
domain fact, not something derivable from the graph.

Origin story (see check_reachability in verify.py for the worked example):
a downstream domain map gave a requires_human_authorization transition its
own dedicated from_state, distinct from its non-destructive twin's. Read cold,
that dedicated from_state looked unreachable -- nothing in the map produced
it -- and the obvious "fix" (merge it onto the twin's shared from_state) broke
four behavior tests, because ThinkingMapTraversal.step() called without an
explicit transition_id aggregates missing_evidence across every transition
sharing a from_state, not just the one the caller meant. The state genuinely
was meant to be entered from outside the graph; the actual defect was that
nothing recorded that on purpose. entry_states exists so that fact is written
down once, in code, instead of being tribal knowledge someone has to
rediscover by breaking tests.
"""

from __future__ import annotations

from collections.abc import Iterable

from fpf_thinking_map.primitives import TransitionPrimitive
from fpf_thinking_map.state import SemanticMap

__all__ = [
    "graph_roots",
    "forward_reachable",
    "shortest_path_distance",
    "biconditional_clear",
    "unreachable_transitions",
]


def graph_roots(transitions: Iterable[TransitionPrimitive]) -> set[str]:
    """States that no declared transition's to_state ever produces.

    Every state in the returned set is either an intentional entry point
    or an orphaned from_state -- this function makes no claim about which.
    Useful for auditing a map you didn't author: it's the candidate list
    to sort into "yes, callers arrive here directly" and "nobody meant
    this," by hand, once, rather than rediscovering it via a break like
    the one described in this module's docstring.
    """
    transitions = list(transitions)
    produced = {t.to_state for t in transitions}
    consumed = {t.from_state for t in transitions}
    return consumed - produced


def forward_reachable(
    transitions: Iterable[TransitionPrimitive],
    entry_states: Iterable[str],
) -> set[str]:
    """States reachable from entry_states by following declared to_state edges.

    Plain BFS over the (from_state -> to_state) graph -- algorithm 10.1's
    graph formulation, forward direction. At domain-map scale (tens of
    edges) this is microseconds; there is no reason to approximate it.
    """
    transitions = list(transitions)
    edges: dict[str, list[str]] = {}
    for t in transitions:
        edges.setdefault(t.from_state, []).append(t.to_state)

    seen = set(entry_states)
    frontier = list(seen)
    while frontier:
        s = frontier.pop()
        for nxt in edges.get(s, []):
            if nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    return seen


def shortest_path_distance(
    transitions: Iterable[TransitionPrimitive],
    source: str,
    target: str,
) -> int | None:
    """BFS hop count from source to target on declared to_state edges.

    Returns 0 when source == target, a non-negative integer hop count when a
    path exists, or None when target is not forward-reachable from source.
    This is the distance check ADV-15 requires for an end_compile_revert
    terminal (``distance <= bound``); ``forward_reachable`` only answers
    set membership and is not a substitute.
    """
    if source == target:
        return 0
    transitions = list(transitions)
    edges: dict[str, list[str]] = {}
    for t in transitions:
        edges.setdefault(t.from_state, []).append(t.to_state)

    dist = {source: 0}
    frontier = [source]
    while frontier:
        s = frontier.pop(0)
        for nxt in edges.get(s, []):
            if nxt not in dist:
                dist[nxt] = dist[s] + 1
                if nxt == target:
                    return dist[nxt]
                frontier.append(nxt)
    return None


def biconditional_clear(
    transitions: Iterable[TransitionPrimitive],
    percept_state: str,
    percept_absent: bool,
    *,
    strict_state_ids: bool = False,
) -> set[str]:
    """Wumpus-World-style negative-evidence inference (ADV-17): given a
    declared percept is CONFIRMED absent at percept_state, return every
    state adjacent to it that a biconditional therefore proves danger-free.

    Adjacency here is UNDIRECTED -- deliberately not the directed relation
    shortest_path_distance/forward_reachable use, since the biconditional
    this models (``Percept(p, c*) <=> OR(D(c) for c adjacent to c*)``) is
    symmetric: a transition declared c1->c2 makes c1 and c2 mutually
    adjacent for this inference, regardless of which direction it fires.

    Returns the empty set when percept_absent is False -- this function
    computes the graph-membership half of the inference only. It does not
    decide what "danger-free" should be allowed to unlock; same split as
    shortest_path_distance vs. a guard's distance<=bound policy (ADV-15).
    Whether a specific percept_state was confirmed absent (vs. merely
    unconfirmed) is a state.py concern (see ActiveState.confirm_percept_absent
    and the ADV-03 discussion in PROPOSED_WUMPUS_ADJACENCY_CLEARANCE.md), not
    this function's -- this function is pure and knows nothing about evidence.

    strict_state_ids (ADV-07): when True, percept_state not appearing as
    either endpoint of any declared transition raises ValueError instead of
    silently returning an empty set. Default stays permissive/fail-safe --
    under-clearing (nothing proven safe) is the safe direction to fail in,
    never over-clearing.
    """
    if not percept_absent:
        return set()
    transitions = list(transitions)
    neighbors: set[str] = set()
    known_states: set[str] = set()
    for t in transitions:
        known_states.add(t.from_state)
        known_states.add(t.to_state)
        if t.from_state == percept_state:
            neighbors.add(t.to_state)
        if t.to_state == percept_state:
            neighbors.add(t.from_state)
    if strict_state_ids and percept_state not in known_states:
        raise ValueError(
            f"percept_state '{percept_state}' is not an endpoint of any "
            "declared transition"
        )
    return neighbors


def unreachable_transitions(
    sm: SemanticMap,
    entry_states: Iterable[str],
) -> list[TransitionPrimitive]:
    """Transitions whose from_state is unreachable given the declared entry points.

    entry_states must be supplied explicitly. Omitting a state that a
    caller genuinely does set current_state to directly is not a bug in
    this function -- it is the intended failure mode, surfacing every
    undeclared entry point by name instead of silently accepting it. See
    check_reachability in verify.py for both directions demonstrated: the
    library's own build_destructive_action_map() example map is clean when
    "reviewed" is declared as an entry point, and loudly not clean when it
    isn't.

    Returns transitions in registration order (dict-ordered, matching
    SemanticMap.transitions), not sorted -- callers building error messages
    generally want map-declaration order, not alphabetical.
    """
    transitions = list(sm.transitions.values())
    reachable = forward_reachable(transitions, entry_states)
    return [t for t in transitions if t.from_state not in reachable]
