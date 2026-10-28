# Copyright (c) 2026 CONSOLIDARE CONTINUUM S.R.L. <info@consolidare-continuum.com>
# SPDX-License-Identifier: MIT
"""Traversal checkpoint and restore — hand a paused ActiveState back to the engine intact.

`ActiveState` keeps three counters (`_evidence_added_at`, `_state_visits`,
`_state_visit_evidence`) and a few more private records that no constructor
accepts. A host that persists a session by hand-rolling a rebuild produces a
structurally valid state that has forgotten every prior visit: evidence TTL
decay and stagnation counting silently reset across exactly the boundary
(idle resume, context compaction, process restart) a host most wants them
kept (ADV-08). This module is the supported round trip.

`build_checkpoint()` / `restore_from_checkpoint()` are observational: neither
ticks `step_count`, registers a visit, adds evidence, nor fires a transition.
Restore is all-or-nothing — any inconsistency raises, nothing is repaired.

Not a trust boundary on its own. A checkpoint is plain JSON and anyone who
can write one can write a self-consistent lie (ADV-03's shape). It lets a
harness that *holds* its own state keep that state faithful; the harness
still decides where the checkpoint lives and who may replace it. See
docs/deep/DESIGN_TRAVERSAL_CHECKPOINT.md.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from collections.abc import Mapping
from enum import Enum
from typing import TYPE_CHECKING, Any

from fpf_thinking_map.agentic_structure import AutonomyLedgerEntry
from fpf_thinking_map.pending_input import PendingInput, PendingInputStatus

if TYPE_CHECKING:
    from fpf_thinking_map.state import ActiveState, SemanticMap

SCHEMA_VERSION = "1"

_TOP_KEYS = {"schema_version", "map_fingerprint", "orientation", "binding", "active"}
_ACTIVE_KEYS = {
    "current_state", "step_count", "stagnation_threshold",
    "pending_authorizations", "denied_authorizations", "consumed_authorizations",
    "authorization_clock", "autonomy_ledger", "evidence_added_at",
    "state_visits", "state_visit_evidence", "adjacency_clearances",
    "confirmed_absent_percepts", "trace",
}


class CheckpointError(ValueError):
    """Base class for every checkpoint build/restore failure."""


class UnsupportedCheckpointVersion(CheckpointError):
    pass


class MapFingerprintMismatch(CheckpointError):
    pass


class InvalidCheckpointState(CheckpointError):
    pass


def to_jsonable(obj: Any) -> Any:
    """Plain-data projection used for both fingerprints and checkpoints.

    Fails closed: anything that is not data (a callable, an arbitrary
    object) raises TypeError instead of being stringified, so a fingerprint
    can never silently ignore part of a map.
    """
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, Enum):
        return obj.value
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {
            f.name: to_jsonable(getattr(obj, f.name))
            for f in dataclasses.fields(obj)
            if not f.name.startswith("_")
        }
    if isinstance(obj, Mapping):
        return {str(k): to_jsonable(v) for k, v in sorted(obj.items(), key=lambda kv: str(kv[0]))}
    if isinstance(obj, (set, frozenset)):
        return sorted((to_jsonable(v) for v in obj), key=lambda v: json.dumps(v, sort_keys=True))
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    raise TypeError(f"not plain data: {type(obj).__name__}")


_MAP_SECTIONS = (
    "contexts", "roles", "role_assignments", "work_records", "work_plans",
    "speech_acts", "commitments", "gates", "evidence", "transitions",
    "publications", "call_plans", "autonomy_budgets", "adjacency_clearance_rules",
)


def map_fingerprint(semantic_map: "SemanticMap") -> str:
    """SHA-256 over every registered primitive of the map.

    Computed on demand, never cached: the registries are plain dicts that a
    caller can mutate without going through register_*(), and a stale
    fingerprint would let a checkpoint restore against a map it no longer
    describes.
    """
    payload = {name: to_jsonable(getattr(semantic_map, name)) for name in _MAP_SECTIONS}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _binding_to_dict(binding: Any) -> dict[str, Any]:
    out = {f.name: to_jsonable(getattr(binding, f.name)) for f in dataclasses.fields(binding)}
    try:
        json.dumps(out)
    except TypeError as exc:
        raise InvalidCheckpointState(f"binding is not JSON-compatible: {exc}") from exc
    return out


def build_checkpoint(state: "ActiveState") -> dict[str, Any]:
    """Serialize everything needed to resume this traversal, and nothing else."""
    fingerprint = map_fingerprint(state.semantic_map)
    trace = state.trace
    return {
        "schema_version": SCHEMA_VERSION,
        "map_fingerprint": fingerprint,
        "orientation": {
            "map_revision": fingerprint,
            "binding_revision": state.binding_revision,
            "computed_at_step": state.step_count,
        },
        "binding": _binding_to_dict(state.binding),
        "active": {
            "current_state": state.current_state,
            "step_count": state.step_count,
            "stagnation_threshold": state.stagnation_threshold,
            "pending_authorizations": sorted(state.pending_authorizations),
            "denied_authorizations": dict(sorted(state.denied_authorizations.items())),
            "consumed_authorizations": sorted(state.consumed_authorizations),
            "authorization_clock": state._authorization_clock,
            "autonomy_ledger": [to_jsonable(e) for e in state.autonomy_ledger],
            "evidence_added_at": dict(sorted(state._evidence_added_at.items())),
            "state_visits": dict(sorted(state._state_visits.items())),
            "state_visit_evidence": {
                k: sorted(v) for k, v in sorted(state._state_visit_evidence.items())
            },
            "adjacency_clearances": {
                k: dict(sorted(v.items())) for k, v in sorted(state._adjacency_clearances.items())
            },
            "confirmed_absent_percepts": dict(sorted(state._confirmed_absent_percepts.items())),
            "trace": {
                "previous_state": trace.previous_state,
                "last_transition_id": trace.last_transition_id,
                "bridge_target": trace.bridge_target,
                "blockers": list(trace.blockers),
                "evidence_delta": list(trace.evidence_delta),
                "move_id": trace.move_id,
                "parent_move_id": trace.parent_move_id,
            },
        },
    }


def _known_states(semantic_map: "SemanticMap", context_id: str) -> set[str]:
    states: set[str] = set()
    for t in semantic_map.transitions.values():
        if t.context_id == context_id:
            states.add(t.from_state)
            states.add(t.to_state)
    return states


def _require(cond: bool, message: str) -> None:
    if not cond:
        raise InvalidCheckpointState(message)


def _is_str_list(v: Any) -> bool:
    return isinstance(v, list) and all(isinstance(x, str) for x in v)


def _is_int_map(v: Any) -> bool:
    return isinstance(v, dict) and all(
        isinstance(k, str) and isinstance(n, int) and not isinstance(n, bool) for k, n in v.items()
    )


def _validate(semantic_map: "SemanticMap", cp: Any, strict: bool) -> None:
    _require(isinstance(cp, dict), "checkpoint must be a dict")
    if cp.get("schema_version") != SCHEMA_VERSION:
        raise UnsupportedCheckpointVersion(
            f"schema_version {cp.get('schema_version')!r} unsupported (only {SCHEMA_VERSION!r})"
        )
    _require(_TOP_KEYS <= set(cp), f"missing top-level keys: {sorted(_TOP_KEYS - set(cp))}")
    _require(isinstance(cp["binding"], dict), "binding must be a dict")
    active = cp["active"]
    _require(isinstance(active, dict), "active must be a dict")
    _require(_ACTIVE_KEYS <= set(active), f"missing active keys: {sorted(_ACTIVE_KEYS - set(active))}")

    if cp["map_fingerprint"] != map_fingerprint(semantic_map):
        raise MapFingerprintMismatch("checkpoint was taken against a different map")

    ctx_id = cp["binding"].get("active_context_id")
    _require(ctx_id in semantic_map.contexts, f"unknown active_context_id {ctx_id!r}")
    state = active["current_state"]
    _require(isinstance(state, str), "current_state must be a string")
    _require(state in _known_states(semantic_map, ctx_id),
             f"state {state!r} is not a known state of context {ctx_id!r}")

    evidence = cp["binding"].get("current_evidence", [])
    _require(_is_str_list(evidence), "current_evidence must be a list of strings")
    if strict:
        unknown = sorted(set(evidence) - set(semantic_map.evidence))
        _require(not unknown, f"evidence ids not registered on the map: {unknown}")

    step = active["step_count"]
    _require(isinstance(step, int) and not isinstance(step, bool) and step >= 0,
             "step_count must be a non-negative int")
    _require(isinstance(active["stagnation_threshold"], int), "stagnation_threshold must be an int")
    clock = active["authorization_clock"]
    _require(isinstance(clock, int) and clock >= 0, "authorization_clock must be a non-negative int")

    _require(_is_int_map(active["evidence_added_at"]), "evidence_added_at must map str -> int")
    _require(all(v <= step for v in active["evidence_added_at"].values()),
             "evidence_added_at holds a step in the future")
    _require(_is_int_map(active["state_visits"]), "state_visits must map str -> int")
    _require(all(v >= 0 for v in active["state_visits"].values()), "state_visits has a negative count")
    sve = active["state_visit_evidence"]
    _require(isinstance(sve, dict) and all(isinstance(k, str) and _is_str_list(v) for k, v in sve.items()),
             "state_visit_evidence must map str -> list[str]")

    for key in ("pending_authorizations", "consumed_authorizations"):
        _require(_is_str_list(active[key]), f"{key} must be a list of strings")
    _require(isinstance(active["denied_authorizations"], dict), "denied_authorizations must be a dict")
    for tid in list(active["pending_authorizations"]) + list(active["denied_authorizations"]):
        _require(tid in semantic_map.transitions, f"authorization names unknown transition {tid!r}")

    trace = active["trace"]
    _require(isinstance(trace, dict), "trace must be a dict")
    last = trace.get("last_transition_id")
    _require(last is None or last in semantic_map.transitions, f"trace names unknown transition {last!r}")
    bridge = trace.get("bridge_target")
    _require(bridge is None or bridge in semantic_map.contexts, f"trace names unknown context {bridge!r}")

    orient = cp["orientation"]
    _require(isinstance(orient, dict), "orientation must be a dict")
    _require(orient.get("map_revision") == cp["map_fingerprint"], "orientation.map_revision disagrees with fingerprint")
    _require(orient.get("computed_at_step") == step, "orientation.computed_at_step disagrees with step_count")


def restore_from_checkpoint(
    semantic_map: "SemanticMap", checkpoint: dict[str, Any], *, strict: bool = True,
) -> "ActiveState":
    """Rebuild an ActiveState exactly as it was checkpointed, or raise.

    strict=True (default) also requires every bound evidence id to be a
    registered evidence primitive. A harness that deliberately binds
    unregistered tokens passes strict=False; nothing else is relaxed.
    """
    from fpf_thinking_map.state import ActiveState, MoveTrace, RuntimeBinding

    _validate(semantic_map, checkpoint, strict)
    active = checkpoint["active"]
    raw = dict(checkpoint["binding"])

    known = {f.name for f in dataclasses.fields(RuntimeBinding)}
    extra = sorted(set(raw) - known)
    _require(not extra, f"binding has unknown fields: {extra}")
    try:
        raw["pending_inputs"] = [
            PendingInput(**{**pi, "status": PendingInputStatus(pi["status"])})
            for pi in raw.get("pending_inputs", [])
        ]
        binding = RuntimeBinding(**raw)
        ledger = [AutonomyLedgerEntry(**e) for e in active["autonomy_ledger"]]
        tr = active["trace"]
        trace = MoveTrace(
            previous_state=tr.get("previous_state"),
            last_transition_id=tr.get("last_transition_id"),
            bridge_target=tr.get("bridge_target"),
            blockers=list(tr.get("blockers", [])),
            evidence_delta=list(tr.get("evidence_delta", [])),
            move_id=tr.get("move_id"),
            parent_move_id=tr.get("parent_move_id"),
        )
    except (TypeError, ValueError, KeyError) as exc:
        raise InvalidCheckpointState(f"checkpoint payload does not decode: {exc}") from exc

    state = ActiveState(
        semantic_map=semantic_map,
        binding=binding,
        current_state=active["current_state"],
        trace=trace,
        step_count=active["step_count"],
        stagnation_threshold=active["stagnation_threshold"],
        pending_authorizations=set(active["pending_authorizations"]),
        consumed_authorizations=set(active["consumed_authorizations"]),
        denied_authorizations=dict(active["denied_authorizations"]),
        autonomy_ledger=ledger,
    )
    # __post_init__ stamped every bound evidence id at step 0; the checkpoint is authoritative.
    state._evidence_added_at = dict(active["evidence_added_at"])
    state._state_visits = dict(active["state_visits"])
    state._state_visit_evidence = {k: frozenset(v) for k, v in active["state_visit_evidence"].items()}
    state._adjacency_clearances = {k: dict(v) for k, v in active["adjacency_clearances"].items()}
    state._confirmed_absent_percepts = dict(active["confirmed_absent_percepts"])
    state._authorization_clock = active["authorization_clock"]
    state.map_revision = checkpoint["map_fingerprint"]
    state.binding_revision = checkpoint["orientation"].get("binding_revision", 0)
    return state
